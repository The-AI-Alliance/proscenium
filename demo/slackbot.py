#!/usr/bin/env python3

from typing import Optional
import os
import time
import logging

from rich.pretty import pprint
from rich.console import Console

from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.web import WebClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from proscenium.verbs.display import header

from demo.slack.handlers import start_handlers, stop_handlers, prerequisites


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


if __name__ == "__main__":

    verbose = True  # TODO make this a command line option
    console = Console()
    sub_console = None

    if verbose:
        logging.basicConfig(level=logging.INFO)
        sub_console = console
    else:
        logging.basicConfig(level=logging.WARN)

    console.print(header())

    console.print("Starting the Proscenium Slack bot demo...")

    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")

    web_client = WebClient(token=slack_bot_token)
    socket_mode_client = SocketModeClient(
        app_token=slack_app_token, web_client=web_client
    )

    socket_mode_client.connect()
    console.print("Connected.")

    subscribed_channels = socket_mode_client.web_client.conversations_list(
        types="public_channel,private_channel,mpim,im",
        limit=1000,
    )

    channels_by_id = {
        channel["id"]: channel for channel in subscribed_channels["channels"]
    }

    auth_response = socket_mode_client.web_client.auth_test()

    console.print(auth_response["url"])
    console.print()
    console.print(f"Team '{auth_response["team"]}' ({auth_response["team_id"]})")
    console.print(f"User '{auth_response["user"]}' ({auth_response["user_id"]})")

    user_id = auth_response["user_id"]
    console.print("Bot id", auth_response["bot_id"])

    console.print("Building any missing resouces...")
    pres = prerequisites(console=sub_console)
    for pre in pres:
        pre()

    console.print("Starting handlers...")
    channel_to_handler = start_handlers(console=sub_console)

    console.print()
    console.print(
        "Handlers defined for channels:", ", ".join(list(channel_to_handler.keys()))
    )

    slack_listener = make_slack_listener(
        user_id, channels_by_id, channel_to_handler, console
    )
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

    socket_mode_client.web_client.chat_postMessage(
        channel=user_id,
        text="Shutting down.",
    )

    socket_mode_client.socket_mode_request_listeners.remove(slack_listener)
    socket_mode_client.disconnect()
    console.print("Disconnected.")

    stop_handlers()
    console.print("Handlers stopped.")
