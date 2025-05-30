#!/usr/bin/env python3

import typer
import time
import os
import sys
import logging
from pathlib import Path
from rich.console import Console

from proscenium.verbs.display import header
from proscenium.bin import production_from_config
from proscenium.interfaces.slack import SlackProductionProcessor

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s  %(levelname)-8s %(name)s: %(message)s",
    level=logging.WARNING,
)

app = typer.Typer(help="Proscenium Bot")

log = logging.getLogger(__name__)

default_config_path = Path("demo/demo.yml")


@app.command(help="""Start the Proscenium Bot.""")
def start(
    config_file: Path = typer.Option(
        default_config_path,
        help="The name of the Proscenium YAML configuration file.",
    ),
    verbose: bool = False,
):

    console = Console()
    sub_console = None

    if verbose:
        log.setLevel(logging.INFO)
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = console

    console.print(header())

    production, config = production_from_config(
        config_file, os.environ.get, sub_console
    )

    console.print("Preparing props...")
    production.prepare_props()
    console.print("Props are up-to-date.")

    slack_admin_channel = config.get("slack", {}).get("admin_channel", None)
    slack_production_processor = SlackProductionProcessor(
        production,
        slack_admin_channel,
        console,
    )

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("Exiting...")

    slack_production_processor.shutdown()


if __name__ == "__main__":

    app()
