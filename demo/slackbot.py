#!/usr/bin/env python3

import os
import time
from rich import print

from rich.pretty import pprint

from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.web import WebClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from proscenium.verbs.display import header

from demo.slack.handlers import start_handlers, stop_handlers


def make_slack_listener(
    self_user_id: str, channels_by_id: dict, channel_to_handler: dict
):

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
                print(user, "in", "#" + channel["name"], "said ", f'"{text}"')

                response = None
                if channel is None:
                    # TODO: channels_by_id will get stale
                    pass
                else:
                    channel_name = channel["name"]
                    if channel_name in channel_to_handler:
                        handle = channel_to_handler[channel_name]
                        print("Handler defined for channel", channel_name)
                        # TODO determine whether the handler has a good chance of being useful
                        for response in handle(text):
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

    print(header())

    print("Starting the Proscenium Slack bot demo...")

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

    print(auth_response["url"])
    print()
    print(f"Team '{auth_response["team"]}' ({auth_response["team_id"]})")
    print(f"User '{auth_response["user"]}' ({auth_response["user_id"]})")

    user_id = auth_response["user_id"]
    print("Bot id", auth_response["bot_id"])

    print("Starting handlers...")
    channel_to_handler = start_handlers(verbose=True)

    print()
    print("Handlers defined for channels:", ", ".join(list(channel_to_handler.keys())))

    slack_listener = make_slack_listener(user_id, channels_by_id, channel_to_handler)
    socket_mode_client.socket_mode_request_listeners.append(slack_listener)
    print("Listening for events...")

    socket_mode_client.web_client.chat_postMessage(
        channel=user_id,
        text="Starting up.",
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")

    socket_mode_client.web_client.chat_postMessage(
        channel=user_id,
        text="Shutting down.",
    )

    socket_mode_client.socket_mode_request_listeners.remove(slack_listener)
    socket_mode_client.disconnect()
    print("Disconnected.")

    stop_handlers()
    print("Handlers stopped.")
