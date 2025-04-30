#!/usr/bin/env python3

from typing import Any
import os
import logging
import typer
from rich.console import Console

from proscenium.interfaces.slack import (
    build_resources,
    bot_user_id,
    channel_map,
    make_slack_listener,
    connect,
    listen,
    shutdown,
)

from proscenium.verbs.display import header

from demo.slack.handlers import start_handlers, stop_handlers, prerequisites

app = typer.Typer(help="Proscenium Slackbot")


@app.command(help=f"""Start the Proscenium Slackbot.""")
def start(verbose: bool = False, force_rebuild: bool = False):

    console = Console()
    sub_console = None

    if verbose:
        logging.basicConfig(level=logging.INFO)
        sub_console = console
    else:
        logging.basicConfig(level=logging.WARN)

    console.print(header())
    console.print("Starting the Proscenium Slackbot.")

    build_resources(prerequisites, console, sub_console, force_rebuild)

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

    shutdown(
        socket_mode_client, slack_listener, user_id, stop_handlers, resources, console
    )


if __name__ == "__main__":

    app()
