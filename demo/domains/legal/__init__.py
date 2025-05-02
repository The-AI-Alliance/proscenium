from typing import Optional
from typing import List
from typing import Callable

import logging
from pathlib import Path

from rich.console import Console


from .docs import default_docs_per_dataset, hf_dataset_ids
from .doc_enricher import default_delay
from .doc_enricher import make_document_enricher
from .kg_loader import make_kg_loader
from .kg_displayer import make_kg_displayer
from .entity_resolvers import default_embedding_model_id
from .entity_resolver_loader import make_entity_resolver_loader
from .query_handler import make_handler, user_prompt, default_question

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


def prerequisites(
    docs_per_dataset: int,
    enrichment_jsonl_file: Path,
    delay: float,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    milvus_uri: str,
    embedding_model_id: str,
    console: Optional[Console] = None,
) -> List[Callable[[bool], None]]:

    enrich = make_document_enricher(
        docs_per_dataset, enrichment_jsonl_file, delay, console
    )

    load_kg = make_kg_loader(
        enrichment_jsonl_file, neo4j_uri, neo4j_username, neo4j_password, console
    )

    load_resolver = make_entity_resolver_loader(
        milvus_uri,
        embedding_model_id,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        console,
    )

    return [
        enrich,
        load_kg,
        load_resolver,
    ]
