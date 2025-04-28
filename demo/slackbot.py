#!/usr/bin/env python3

from typing import Any
import os
import time
import logging
import typer

from rich.pretty import pprint
from rich.console import Console


from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.listeners import SocketModeRequestListener

from proscenium.verbs.display import header

from demo.slack.handlers import start_handlers, stop_handlers, prerequisites

app = typer.Typer(help="Proscenium Slackbot")


def build_resources(console: Console, sub_console: Console = None):

    console.print("Building any missing resouces...")

    pres = prerequisites(console=sub_console)
    for pre in pres:
        pre()


def connect(app_token: str, bot_token: str, console: Console) -> SocketModeClient:

    web_client = WebClient(token=bot_token)
    socket_mode_client = SocketModeClient(app_token=app_token, web_client=web_client)

    socket_mode_client.connect()
    console.print("Connected.")

    return socket_mode_client


def make_slack_listener(
    self_user_id: str,
    channels_by_id: dict,
    channel_to_handler: dict,
    console: Console,
):

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
                channel_id = event.get("channel")

                channel = channels_by_id.get(channel_id, None)
                console.print(user, "in", "#" + channel["name"], "said ", f'"{text}"')

                response = None
                if channel is None:
                    # TODO: channels_by_id will get stale
                    pass
                else:
                    channel_name = channel["name"]
                    if channel_name in channel_to_handler:
                        handle = channel_to_handler[channel_name]
                        console.print("Handler defined for channel", channel_name)
                        # TODO determine whether the handler has a good chance of being useful
                        for response in handle(text):
                            console.print("Sending response to channel:", response)
                            client.web_client.chat_postMessage(
                                channel=channel_id, text=response
                            )
                    else:
                        logging.warning("No handler for channel", channel_name)

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


def channel_map(socket_mode_client: SocketModeClient) -> dict:

    subscribed_channels = socket_mode_client.web_client.conversations_list(
        types="public_channel,private_channel,mpim,im",
        limit=1000,
    )

    channels_by_id = {
        channel["id"]: channel for channel in subscribed_channels["channels"]
    }

    return channels_by_id


def bot_user_id(socket_mode_client: SocketModeClient, console: Console):

    auth_response = socket_mode_client.web_client.auth_test()

    console.print(auth_response["url"])
    console.print()
    console.print(f"Team '{auth_response["team"]}' ({auth_response["team_id"]})")
    console.print(f"User '{auth_response["user"]}' ({auth_response["user_id"]})")

    user_id = auth_response["user_id"]
    console.print("Bot id", auth_response["bot_id"])

    return user_id


def listen(
    socket_mode_client: SocketModeClient,
    slack_listener: SocketModeRequestListener,
    user_id: str,
    console: Console,
):
    socket_mode_client.socket_mode_request_listeners.append(slack_listener)

    console.print("Listening for events...")
    socket_mode_client.web_client.chat_postMessage(
        channel=user_id,
        text="Starting up.",
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("Exiting...")


def shutdown(
    socket_mode_client: SocketModeClient,
    slack_listener: SocketModeRequestListener,
    user_id: str,
    resources: Any,
    console: Console,
):

    socket_mode_client.web_client.chat_postMessage(
        channel=user_id,
        text="Shutting down.",
    )

    socket_mode_client.socket_mode_request_listeners.remove(slack_listener)
    socket_mode_client.disconnect()
    console.print("Disconnected.")

    stop_handlers(resources)
    console.print("Handlers stopped.")


@app.command(help=f"""Start the Proscenium Slackbot.""")
def start(verbose: bool = False):

    console = Console()
    sub_console = None

    if verbose:
        logging.basicConfig(level=logging.INFO)
        sub_console = console
    else:
        logging.basicConfig(level=logging.WARN)

    console.print(header())
    console.print("Starting the Proscenium Slackbot.")

    build_resources(console, sub_console)

    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    socket_mode_client = connect(slack_app_token, slack_bot_token, console)

    channels_by_id = channel_map(socket_mode_client)

    user_id = bot_user_id(socket_mode_client, console)

    channel_to_handler, resources = start_handlers(console=sub_console)

    slack_listener = make_slack_listener(
        user_id, channels_by_id, channel_to_handler, console
    )

    listen(
        socket_mode_client,
        slack_listener,
        user_id,
        console,
    )

    shutdown(socket_mode_client, slack_listener, user_id, resources, console)


if __name__ == "__main__":

    app()
