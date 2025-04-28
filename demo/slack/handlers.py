from typing import Generator
from typing import Callable
from typing import List

from pathlib import Path
import os

from proscenium.verbs.know import knowledge_graph_client

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


# TODO create `prerequisites` function in each domain
def prerequisites(verbose: bool = False) -> List[Callable[[], None]]:

    # Literature

    build = literature_domain.make_chunk_space_builder(
        literature_milvus_uri,
        literature_domain.default_collection_name,
        literature_domain.default_embedding_model_id,
        verbose=verbose,
    )

    # Legal

    enrich = legal_domain.make_document_enricher(4, enrichment_jsonl_file, 0.1, verbose)

    load_kg = legal_domain.make_kg_loader(
        enrichment_jsonl_file, neo4j_uri, neo4j_username, neo4j_password, verbose
    )

    load_resolver = legal_domain.make_entity_resolver_loader(
        legal_milvus_uri,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        verbose,
    )

    return [
        build,
        enrich,
        load_kg,
        load_resolver,
    ]


def start_handlers(
    verbose: bool = False,
) -> dict[str, Callable[[str], Generator[str, None, None]]]:

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
