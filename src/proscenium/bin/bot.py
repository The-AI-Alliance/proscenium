#!/usr/bin/env python3

import os
import sys
import logging
import typer
from pathlib import Path
from rich.console import Console

from proscenium.verbs.display import header
from proscenium.bin import production_from_config
from proscenium.interfaces.slack import slack_main

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

    slack_main(production, config, console)


if __name__ == "__main__":

    app()
