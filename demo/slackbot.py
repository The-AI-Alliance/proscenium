#!/usr/bin/env python3

from typing import Optional
import os
import time
from pathlib import Path
from rich import print

from rich.pretty import pprint

from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.web import WebClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from proscenium.verbs.complete import complete_simple
from proscenium.verbs.know import knowledge_graph_client
from proscenium.scripts.graph_rag import query_to_prompts

default_enrichment_jsonl_file = Path("enrichments.jsonl")
default_neo4j_uri = "bolt://localhost:7687"
default_neo4j_username = "neo4j"
default_neo4j_password = "password"
default_milvus_uri = "file:/grag-milvus.db"

neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)
milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)


def handle_abacus(question: str, verbose: bool = False) -> Optional[str]:

    from proscenium.verbs.invoke import process_tools
    from proscenium.scripts.tools import apply_tools

    from gofannon.basic_math.addition import Addition
    from gofannon.basic_math.subtraction import Subtraction
    from gofannon.basic_math.multiplication import Multiplication
    from gofannon.basic_math.division import Division

    tools = [Addition, Subtraction, Multiplication, Division]

    tool_map, tool_desc_list = process_tools(tools)

    from demo.config import default_model_id

    answer = apply_tools(
        model_id=default_model_id,
        system_message=""""
Use the tools specified in this request to perform the arithmetic in the user's question.
Do not use any other tools.
""",
        message=question,
        tool_desc_list=tool_desc_list,
        tool_map=tool_map,
        rich_output=verbose,
    )

    return answer


def handle_literature(question: str, verbose: bool = False) -> Optional[str]:

    from proscenium.verbs.vector_database import embedding_function
    from proscenium.verbs.vector_database import vector_db

    from proscenium.scripts.rag import answer_question
    from proscenium.scripts.chunk_space import build_vector_db as bvd
    import demo.domains.literature as domain

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    collection_name = "literature_chunks"

    vector_db_client = vector_db(milvus_uri)
    print("Vector db at uri", milvus_uri)

    embedding_fn = embedding_function(domain.embedding_model_id)
    print("Embedding model:", domain.embedding_model_id)

    answer = answer_question(
        question,
        domain.model_id,
        vector_db_client,
        embedding_fn,
        collection_name,
        verbose,
    )

    return answer


def handle_legal(question: str, verbose: bool = False) -> Optional[str]:

    import demo.domains.legal as domain

    prompts = query_to_prompts(
        question,
        domain.default_query_extraction_model_id,
        milvus_uri,
        driver,
        domain.query_extract,
        domain.query_extract_to_graph,
        domain.query_extract_to_context,
        domain.context_to_prompts,
        verbose,
    )

    if prompts is None:

        print("Unable to form prompts")
        return None

    else:

        system_prompt, user_prompt = prompts

        response = complete_simple(
            domain.default_generation_model_id,
            system_prompt,
            user_prompt,
            rich_output=verbose,
        )

        return response


def make_process(self_user_id: str, channels_by_id: dict, channel_to_handler: dict):

    def process(client: SocketModeClient, req: SocketModeRequest):

        # pprint(req.__dict__)

        if req.type == "events_api":

            event = req.payload["event"]

            response = SocketModeResponse(envelope_id=req.envelope_id)
            client.send_socket_mode_response(response)

            if event.get("type") in [
                "message",
                "app_mention",
            ]:
                user = event.get("user")
                if user == self_user_id:
                    return

                text = event.get("text")
                channel_id = event.get("channel")

                channel = channels_by_id.get(channel_id, None)
                print(user, "in", "#" + channel["name"], "said", text)

                response = None
                if channel is None:
                    # TODO: channels_by_id will get stale
                    pass
                else:
                    channel_name = channel["name"]
                    if channel_name in channel_to_handler:
                        handler = channel_to_handler[channel_name]
                        print("Handler defined for channel", channel_name)
                        # TODO determine whether the handler has a good chance of being useful
                        response = handler(text, verbose=True)
                        if response is not None:
                            print("Sending response to channel:", response)
                            client.web_client.chat_postMessage(
                                channel=channel_id, text=response
                            )
                    else:
                        print("No handler for channel", channel_name)

        elif req.type == "interactive":
            pass
        elif req.type == "slash_commands":
            pass
        elif req.type == "app_home_opened":
            pass
        elif req.type == "block_actions":
            pass
        elif req.type == "message_actions":
            pass

    return process


if __name__ == "__main__":

    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")

    web_client = WebClient(token=slack_bot_token)
    socket_mode_client = SocketModeClient(
        app_token=slack_app_token, web_client=web_client
    )

    socket_mode_client.connect()
    print("Connected.")

    subscribed_channels = socket_mode_client.web_client.conversations_list(
        types="public_channel,private_channel,mpim,im",
        limit=1000,
    )

    channels_by_id = {
        channel["id"]: channel for channel in subscribed_channels["channels"]
    }

    auth_response = socket_mode_client.web_client.auth_test()

    bot_user_id = auth_response["user_id"]

    print("URL:", auth_response["url"])
    print("Bot ID:", auth_response["bot_id"])
    print("Team:", auth_response["team"], "ID:", auth_response["team_id"])
    print("User:", auth_response["user"], "ID:", auth_response["user_id"])

    channel_to_handler = {
        "legal": handle_legal,
        "abacus": handle_abacus,
        "literature": handle_literature,
    }
    print("Handlers defined for channels:", ", ".join(list(channel_to_handler.keys())))

    process = make_process(bot_user_id, channels_by_id, channel_to_handler)
    socket_mode_client.socket_mode_request_listeners.append(process)
    print("Listening for events...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

    socket_mode_client.socket_mode_request_listeners.remove(process)
    socket_mode_client.disconnect()
    print("Disconnected.")
    driver.close()
    print("Driver closed.")
