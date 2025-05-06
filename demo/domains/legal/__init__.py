from typing import Optional
from typing import List
import logging
from pathlib import Path
from rich.console import Console

from proscenium.core import Prop

from .docs import default_docs_per_dataset, hf_dataset_ids
from .doc_enrichments import default_delay
from .doc_enrichments import DocumentEnrichments
from .kg import CaseLawKnowledgeGraph
from .entity_resolvers import EntityResolvers
from .entity_resolvers import default_embedding_model_id
from .query_handler import user_prompt, default_question

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


def props(
    docs_per_dataset: int,
    enrichment_jsonl_file: Path,
    delay: float,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    milvus_uri: str,
    embedding_model_id: str,
    console: Optional[Console] = None,
) -> List[Prop]:

    doc_enrichments = DocumentEnrichments(
        docs_per_dataset, enrichment_jsonl_file, delay, console
    )

    clkg = CaseLawKnowledgeGraph(
        enrichment_jsonl_file, neo4j_uri, neo4j_username, neo4j_password, console
    )

    entity_resolvers = EntityResolvers(
        milvus_uri,
        embedding_model_id,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        console,
    )

    return [
        doc_enrichments,
        clkg,
        entity_resolvers,
    ]
