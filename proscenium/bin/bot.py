#!/usr/bin/env python3

import os
import sys
import logging
import typer
import importlib
from rich.console import Console

from proscenium.admin import Admin

from proscenium.interfaces.slack import (
    get_slack_auth,
    channel_table,
    bot_user_id,
    places_table,
    channel_maps,
    make_slack_listener,
    connect,
    send_curtain_up,
    listen,
    send_curtain_down,
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

    production_module = importlib.import_module(production_module_name, package=None)

    slack_admin_channel_id = os.environ.get("SLACK_ADMIN_CHANNEL_ID")
    # Note that the checking of the existence of the admin channel id is delayed
    # until after the subscribed channels are shown.

    production = production_module.make_production(slack_admin_channel_id, sub_console)

    console.print("Preparing props...")
    production.prepare_props()
    console.print("Props are up-to-date.")

    slack_app_token, slack_bot_token = get_slack_auth()

    socket_mode_client = connect(slack_app_token, slack_bot_token)

    user_id = bot_user_id(socket_mode_client, console)
    console.print()

    channels_by_id, channel_name_to_id = channel_maps(socket_mode_client)
    console.print(channel_table(channels_by_id))
    console.print()

    if slack_admin_channel_id is None:
        raise ValueError(
            "SLACK_ADMIN_CHANNEL_ID environment variable not set. "
            "Please set it to the channel ID of the Proscenium admin channel."
        )
    if slack_admin_channel_id not in channels_by_id:
        raise ValueError(
            f"Admin channel {slack_admin_channel_id} not found in subscribed channels."
        )

    admin = Admin(slack_admin_channel_id)
    log.info("Admin handler started.")

    log.info("Places, please!")
    channel_id_to_character = production.places(channel_name_to_id)
    channel_id_to_character[slack_admin_channel_id] = admin

    console.print(places_table(channel_id_to_character, channels_by_id))
    console.print()

    slack_listener = make_slack_listener(
        user_id,
        slack_admin_channel_id,
        channels_by_id,
        channel_id_to_character,
        console,
    )

    send_curtain_up(socket_mode_client, production, slack_admin_channel_id)

    console.print("Starting the show. Listening for events...")
    listen(
        socket_mode_client,
        slack_listener,
        user_id,
        console,
    )

    send_curtain_down(socket_mode_client, slack_admin_channel_id)

    shutdown(
        socket_mode_client,
        slack_listener,
        user_id,
        production,
        console,
    )


if __name__ == "__main__":

    app()
