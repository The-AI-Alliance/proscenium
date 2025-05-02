from typing import Callable
from typing import Optional
from typing import List
from typing import Any
import time
import logging

from rich.console import Console
from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.listeners import SocketModeRequestListener

log = logging.getLogger(__name__)


def build_resources(
    prerequisites: Callable[[Optional[Console]], List[Callable[[bool], None]]],
    console: Console,
    sub_console: Console = None,
    force: bool = False,
):

    if force:
        console.print("Forcing rebuild of resources.")
    else:
        console.print("Building any missing resouces...")

    pres = prerequisites(console=sub_console)
    for pre in pres:
        pre(force)


def connect(app_token: str, bot_token: str, console: Console) -> SocketModeClient:

    web_client = WebClient(token=bot_token)
    socket_mode_client = SocketModeClient(app_token=app_token, web_client=web_client)

    socket_mode_client.connect()
    console.print("Connected.")

    return socket_mode_client


def make_slack_listener(
    self_user_id: str,
    channels_by_id: dict,
    channel_id_to_handler: dict,
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
                console.print(f"{user} in {channel_id} said something")

                if channel is None:
                    # TODO: channels_by_id will get stale
                    log.info("No handler for channel id %s", channel_id)
                else:
                    handle = channel_id_to_handler[channel_id]
                    log.info("Handler defined for channel id %s", channel_id)
                    # TODO determine whether the handler has a good chance of being useful
                    for response in handle(text):
                        client.web_client.chat_postMessage(
                            channel=channel_id, text=response
                        )
                        log.info("Response sent to channel %s", channel_id)

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


def channel_maps(socket_mode_client: SocketModeClient) -> tuple[dict, dict]:

    subscribed_channels = socket_mode_client.web_client.users_conversations(
        types="public_channel,private_channel,mpim,im",
        limit=100,
    )
    log.info(
        "Subscribed channels count: %s",
        len(subscribed_channels["channels"]),
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

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("Exiting...")


def shutdown(
    socket_mode_client: SocketModeClient,
    slack_listener: SocketModeRequestListener,
    user_id: str,
    stop_handlers: Callable[[Any], None],
    resources: Any,
    console: Console,
):

    socket_mode_client.socket_mode_request_listeners.remove(slack_listener)
    socket_mode_client.disconnect()
    console.print("Disconnected.")

    stop_handlers(resources)
    console.print("Handlers stopped.")
