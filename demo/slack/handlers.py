from typing import Generator
from typing import Callable

# from pathlib import Path
import os

from proscenium.verbs.know import knowledge_graph_client

import demo.domains.abacus as abacus_domain
import demo.domains.literature as literature_domain
import demo.domains.legal as legal_domain

driver = None


def start_handlers(
    verbose: bool = False,
) -> dict[str, Callable[[str], Generator[str, None, None]]]:

    # enrichment_jsonl_file = Path("enrichments.jsonl")

    legal_milvus_uri = "file:/grag-milvus.db"
    literature_milvus_uri = "file:/milvus.db"

    default_neo4j_uri = "bolt://localhost:7687"
    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    default_neo4j_username = "neo4j"
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    default_neo4j_password = "password"
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    channel_to_handler = {
        "abacus": abacus_domain.make_handler(verbose),
        "literature": literature_domain.make_handler(
            literature_domain.default_generator_model_id,
            literature_milvus_uri,
            literature_domain.default_embedding_model_id,
            verbose,
        ),
        "legal": legal_domain.make_handler(driver, legal_milvus_uri, verbose),
    }

    return channel_to_handler


def stop_handlers() -> None:

    driver.close()
