from typing import Generator
from typing import Callable
from typing import List
from typing import Optional
from typing import Any

from rich.console import Console
from pathlib import Path
import os
from neo4j import GraphDatabase
from neo4j import Driver

import demo.domains.abacus as abacus_domain
import demo.domains.literature as literature_domain
import demo.domains.legal as legal_domain

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


def prerequisites(console: Optional[Console] = None) -> List[Callable[[bool], None]]:

    abacus_pres = abacus_domain.prerequisites(console=console)

    literature_pres = literature_domain.prerequisites(
        literature_milvus_uri,
        literature_domain.default_collection_name,
        legal_domain.default_embedding_model_id,
        console=console,
    )

    legal_pres = legal_domain.prerequisites(
        legal_domain.default_docs_per_dataset,
        enrichment_jsonl_file,
        legal_domain.default_delay,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        legal_milvus_uri,
        legal_domain.default_embedding_model_id,
        console=console,
    )

    return abacus_pres + literature_pres + legal_pres


def start_handlers(
    console: Optional[Console] = None,
) -> tuple[dict[str, Callable[[str], Generator[str, None, None]]], Any]:

    if console is not None:
        console.print("Starting handlers...")

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

    channel_to_handler = {
        "abacus": abacus_domain.make_handler(console=console),
        "literature": literature_domain.make_handler(
            literature_domain.default_generator_model_id,
            literature_milvus_uri,
            literature_domain.default_embedding_model_id,
            console=console,
        ),
        "legal": legal_domain.make_handler(driver, legal_milvus_uri, console=console),
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
