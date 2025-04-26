#!/usr/bin/env python3

import os
import time
from rich import print

from rich.pretty import pprint

from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.web import WebClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse


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

                client.web_client.chat_postMessage(
                    channel=channel, text=f"Hello <@{user}>, you said: {text}"
                )
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
