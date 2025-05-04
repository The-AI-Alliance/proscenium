from typing import Callable, Generator, List, Any

import logging
from pathlib import Path
import os

from rich.console import Console

from neo4j import GraphDatabase
from neo4j import Driver

from demo.domains import admin
from demo.domains import abacus
from demo.domains import literature
from demo.domains import legal

log = logging.getLogger(__name__)

literature_milvus_uri = "file:/milvus.db"

enrichment_jsonl_file = Path("enrichments.jsonl")

legal_milvus_uri = "file:/grag-milvus.db"

default_neo4j_uri = "bolt://localhost:7687"
neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
default_neo4j_username = "neo4j"
neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
default_neo4j_password = "password"
neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)


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


def start_admin_handler(
    admin_channel_id: str,
) -> Callable[[str], Generator[str, None, None]]:

    handler = admin.make_handler(admin_channel_id)

    log.info("Admin handler started.")

    return handler


def start_handlers(
    channels_by_id: dict,
    admin_channel_id: str,
) -> tuple[dict[str, Callable[[str], Generator[tuple[str, str], None, None]]], Any]:

    log.info("Starting handlers...")

    channel_name_to_id = {
        channel["name"]: channel["id"]
        for channel in channels_by_id.values()
        if channel.get("name")
    }

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

    channel_id_to_handler = {
        channel_name_to_id["abacus"]: abacus.make_handler(admin_channel_id),
        channel_name_to_id["literature"]: literature.make_handler(
            literature.default_generator_model_id,
            literature_milvus_uri,
            literature.default_embedding_model_id,
            admin_channel_id,
        ),
        channel_name_to_id["legal"]: legal.make_handler(
            driver, legal_milvus_uri, admin_channel_id
        ),
    }

    log.info(
        "Handlers created for channels: %s",
        ", ".join(list(channel_id_to_handler.keys())),
    )

    resources = driver

    return channel_id_to_handler, resources


def stop_handlers(resources: Any) -> None:

    driver: Driver = resources

    driver.close()
