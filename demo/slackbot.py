#!/usr/bin/env python3

import os
import sys
import logging
import typer
from rich.console import Console

from proscenium.interfaces.slack import (
    build_resources,
    bot_user_id,
    channel_maps,
    make_slack_listener,
    connect,
    listen,
    shutdown,
)

from proscenium.verbs.display import header

from demo.slack_config import (
    prerequisites,
    start_admin_handler,
    start_handlers,
    stop_handlers,
)

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s  %(levelname)-8s %(name)s: %(message)s",
    level=logging.WARNING,
)

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s  %(levelname)-8s %(name)s: %(message)s",
    level=logging.WARNING,
)

app = typer.Typer(help="Proscenium Slackbot")

log = logging.getLogger(__name__)


@app.command(help="""Start the Proscenium Slackbot.""")
def start(verbose: bool = False, force_rebuild: bool = False):

    console = Console()
    sub_console = None

    if verbose:
        log.setLevel(logging.INFO)
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = console

    console.print(header())
    console.print("Starting the Proscenium Slackbot.")

    build_resources(prerequisites, console, sub_console, force_rebuild)

    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    if slack_app_token is None:
        raise ValueError(
            "SLACK_APP_TOKEN environment variable not set. "
            "Please set it to the app token of the Proscenium Slack app."
        )
    slack_bot_token = os.environ.get("SLACK_BOT_TOKEN")
    if slack_bot_token is None:
        raise ValueError(
            "SLACK_BOT_TOKEN environment variable not set. "
            "Please set it to the bot token of the Proscenium Slack app."
        )

    socket_mode_client = connect(slack_app_token, slack_bot_token, console)

    channels_by_id = channel_maps(socket_mode_client)
    slack_admin_channel_id = os.environ.get("SLACK_ADMIN_CHANNEL_ID")
    if slack_admin_channel_id is None:
        raise ValueError(
            "SLACK_ADMIN_CHANNEL_ID environment variable not set. "
            "Please set it to the channel ID of the Proscenium admin channel."
        )

    if slack_admin_channel_id not in channels_by_id:
        console.print("Subscribed channels:", channels_by_id)
        raise ValueError(
            f"Admin channel {slack_admin_channel_id} not found in subscribed channels."
        )
    admin_handler = start_admin_handler()

    user_id = bot_user_id(socket_mode_client, console)

    channel_id_to_handler, resources = start_handlers(channels_by_id)
    channel_id_to_handler[slack_admin_channel_id] = admin_handler

    socket_mode_client.web_client.chat_postMessage(
        channel=slack_admin_channel_id, text="Starting up."
    )

    slack_listener = make_slack_listener(
        user_id, channels_by_id, channel_id_to_handler, console
    )

    listen(
        socket_mode_client,
        slack_listener,
        user_id,
        console,
    )

    socket_mode_client.web_client.chat_postMessage(
        channel=slack_admin_channel_id, text="Shutting down."
    )

    shutdown(
        socket_mode_client, slack_listener, user_id, stop_handlers, resources, console
    )


if __name__ == "__main__":

    app()
