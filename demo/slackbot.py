#!/usr/bin/env python3

from typing import Any
from typing import Callable
from typing import Generator
from typing import List
import os
import sys
import logging
import typer
from pathlib import Path
from rich.console import Console
from neo4j import GraphDatabase
from neo4j import Driver

from demo.domains import abacus
from demo.domains import literature
from demo.domains import legal

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

literature_milvus_uri = "file:/milvus.db"

enrichment_jsonl_file = Path("enrichments.jsonl")

legal_milvus_uri = "file:/grag-milvus.db"

default_neo4j_uri = "bolt://localhost:7687"
neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
default_neo4j_username = "neo4j"
neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
default_neo4j_password = "password"
neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)


driver = None


def prerequisites(console: Console) -> List[Callable[[bool], None]]:

    abacus_pres = abacus.prerequisites(console=console)

    literature_pres = literature.prerequisites(
        literature_milvus_uri,
        literature.default_collection_name,
        legal.default_embedding_model_id,
        console=console,
    )

    legal_pres = legal.prerequisites(
        legal.default_docs_per_dataset,
        enrichment_jsonl_file,
        legal.default_delay,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        legal_milvus_uri,
        legal.default_embedding_model_id,
        console=console,
    )

    return abacus_pres + literature_pres + legal_pres


def start_handlers(
    console: Console,
) -> tuple[dict[str, Callable[[str], Generator[str, None, None]]], Any]:

    if console is not None:
        console.print("Starting handlers...")

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

    channel_to_handler = {
        "abacus": abacus.make_handler(console=console),
        "literature": literature.make_handler(
            literature.default_generator_model_id,
            literature_milvus_uri,
            literature.default_embedding_model_id,
            console=console,
        ),
        "legal": legal.make_handler(driver, legal_milvus_uri, console=console),
    }

    if console is not None:
        console.print(
            "Handlers defined for channels:", ", ".join(list(channel_to_handler.keys()))
        )

    resources = driver

    return channel_to_handler, resources


def stop_handlers(resources: Any) -> None:

    driver: Driver = resources

    driver.close()


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
        sub_console = console

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
