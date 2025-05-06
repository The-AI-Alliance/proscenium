#!/usr/bin/env python3

import os
import sys
import logging
import typer
import importlib
from rich.console import Console

from proscenium.admin import Admin

from proscenium.interfaces.slack import (
    bot_user_id,
    channel_maps,
    make_slack_listener,
    connect,
    listen,
    shutdown,
)

from proscenium.verbs.display import header

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

app = typer.Typer(help="Proscenium Bot")

log = logging.getLogger(__name__)


@app.command(help="""Start the Proscenium Bot.""")
def start(
    verbose: bool = False,
    production_module_name: str = typer.Option(
        "demo.production",
        "-p",
        "--production",
        help="The name of the python module in PYTHONPATH in which the variable production of type proscenium.core.Production is defined.",
    ),
    force_rebuild: bool = False,
):

    console = Console()
    sub_console = None

    if verbose:
        log.setLevel(logging.INFO)
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = console

    console.print(header())
    console.print("Starting the Proscenium Bot.")

    production_module = importlib.import_module(production_module_name, package=None)

    props = production_module.production.props(sub_console)
    if force_rebuild:
        console.print("Forcing rebuild of all props.")
    else:
        console.print("Building any missing props...")

    for prop in props:
        prop.build(force_rebuild)

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

    socket_mode_client = connect(slack_app_token, slack_bot_token)

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

    admin = Admin(slack_admin_channel_id)
    log.info("Admin handler started.")

    channel_id_to_handler, resources = production_module.production.places(
        channels_by_id, slack_admin_channel_id
    )
    channel_id_to_handler[slack_admin_channel_id] = admin

    socket_mode_client.web_client.chat_postMessage(
        channel=slack_admin_channel_id,
        text="""
Curtain up. 🎭 https://the-ai-alliance.github.io/proscenium/""",
    )

    user_id = bot_user_id(socket_mode_client, console)

    slack_listener = make_slack_listener(
        user_id, slack_admin_channel_id, channels_by_id, channel_id_to_handler, console
    )

    listen(
        socket_mode_client,
        slack_listener,
        user_id,
        console,
    )

    socket_mode_client.web_client.chat_postMessage(
        channel=slack_admin_channel_id,
        text="""Curtain down. We hope you enjoyed the show!""",
    )

    shutdown(
        socket_mode_client,
        slack_listener,
        user_id,
        production_module.production,
        resources,
        console,
    )


if __name__ == "__main__":

    app()
