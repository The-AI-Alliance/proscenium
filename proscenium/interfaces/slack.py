from typing import Callable

from typing import Generator
import time
import logging
from rich.console import Console
from rich.table import Table

from slack_sdk.web import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.listeners import SocketModeRequestListener

from proscenium.core import Production
from proscenium.core import Character

log = logging.getLogger(__name__)


def connect(app_token: str, bot_token: str) -> SocketModeClient:

    web_client = WebClient(token=bot_token)
    socket_mode_client = SocketModeClient(app_token=app_token, web_client=web_client)

    socket_mode_client.connect()
    log.info("Connected to Slack.")

    return socket_mode_client


def make_slack_listener(
    proscenium_user_id: str,
    admin_channel_id: str,
    channels_by_id: dict,
    channel_id_to_handler: dict[
        str, Callable[[str, str, str], Generator[tuple[str, str], None, None]]
    ],
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
                speaker_id = event.get("user")
                if speaker_id == proscenium_user_id:
                    return

                text = event.get("text")
                channel_id = event.get("channel")
                console.print(f"{speaker_id} in {channel_id} said something")

                channel = channels_by_id.get(channel_id, None)

                if channel is None:

                    # TODO: channels_by_id will get stale
                    log.info("No handler for channel id %s", channel_id)

                else:

                    character = channel_id_to_handler[channel_id]
                    log.info("Handler defined for channel id %s", channel_id)

                    # TODO determine whether the handler has a good chance of being useful

                    for receiving_channel_id, response in character.handle(
                        channel_id, speaker_id, text
                    ):
                        response_response = client.web_client.chat_postMessage(
                            channel=receiving_channel_id, text=response
                        )
                        permalink = client.web_client.chat_getPermalink(
                            channel=receiving_channel_id,
                            message_ts=response_response["ts"],
                        )["permalink"]

                        log.info(
                            "Response sent to channel %s link %s",
                            receiving_channel_id,
                            permalink,
                        )
                        client.web_client.chat_postMessage(
                            channel=admin_channel_id,
                            text=permalink,
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


def channel_maps(socket_mode_client: SocketModeClient) -> dict[str, dict]:

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


def channel_table(channels_by_id) -> Table:
    channel_table = Table(title="Subscribed channels")
    channel_table.add_column("Channel ID", justify="left")
    channel_table.add_column("Name", justify="left")
    for channel_id, channel in channels_by_id.items():
        channel_table.add_row(
            channel_id,
            channel.get("name", "-"),
        )
    return channel_table


def bot_user_id(socket_mode_client: SocketModeClient, console: Console):

    auth_response = socket_mode_client.web_client.auth_test()

    console.print(auth_response["url"])
    console.print()
    console.print(f"Team '{auth_response["team"]}' ({auth_response["team_id"]})")
    console.print(f"User '{auth_response["user"]}' ({auth_response["user_id"]})")

    user_id = auth_response["user_id"]
    console.print("Bot id", auth_response["bot_id"])

    return user_id


def places_table(
    channel_id_to_character: dict[str, Character], channels_by_id: dict[str, dict]
) -> Table:

    table = Table(title="Characters in place")
    table.add_column("Channel ID", justify="left")
    table.add_column("Channel Name", justify="left")
    table.add_column("Character", justify="left")
    for channel_id, character in channel_id_to_character.items():
        channel = channels_by_id[channel_id]
        table.add_row(channel_id, channel["name"], character.name())

    return table


def listen(
    socket_mode_client: SocketModeClient,
    slack_listener: SocketModeRequestListener,
    user_id: str,
    console: Console,
):
    socket_mode_client.socket_mode_request_listeners.append(slack_listener)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("Exiting...")


def shutdown(
    socket_mode_client: SocketModeClient,
    slack_listener: SocketModeRequestListener,
    user_id: str,
    production: Production,
    console: Console,
):

    socket_mode_client.socket_mode_request_listeners.remove(slack_listener)
    socket_mode_client.disconnect()
    console.print("Disconnected from Slack.")

    production.curtain()

    console.print("Handlers stopped.")
