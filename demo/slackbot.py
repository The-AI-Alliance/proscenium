#!/usr/bin/env python3

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

import demo.domains.legal as domain

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


def ask(question: str = None, verbose: bool = False):

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


def make_process(self_user_id: str):

    def process(client: SocketModeClient, req: SocketModeRequest):

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
                channel = event.get("channel")
                # pprint(event)
                print(user, "in", channel, ":", text)

                response = ask(text, verbose=True)

                if response is not None:
                    client.web_client.chat_postMessage(channel=channel, text=response)

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

    auth_response = socket_mode_client.web_client.auth_test()

    bot_user_id = auth_response["user_id"]

    print("URL:", auth_response["url"])
    print("Bot ID:", auth_response["bot_id"])
    print("Team:", auth_response["team"], "ID:", auth_response["team_id"])
    print("User:", auth_response["user"], "ID:", auth_response["user_id"])

    process = make_process(bot_user_id)
    socket_mode_client.socket_mode_request_listeners.append(process)
    print("Listening for events...")

    while True:
        time.sleep(1)

    socket_mode_client.socket_mode_request_listeners.remove(process)
    socket_mode_client.disconnect()
    print("Disconnected.")
    driver.close()
    print("Driver closed.")
