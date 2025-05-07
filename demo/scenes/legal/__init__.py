from typing import Optional
import logging
from pathlib import Path
from rich.console import Console
from neo4j import GraphDatabase

from proscenium.core import Prop
from proscenium.core import Character
from proscenium.core import Scene

from .docs import default_docs_per_dataset
from .doc_enrichments import DocumentEnrichments, default_delay
from .kg import CaseLawKnowledgeGraph
from .entity_resolvers import EntityResolvers
from .entity_resolvers import default_embedding_model_id
from .query_handler import default_generation_model_id
from .query_handler import LawLibrarian

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


class LawLibrary(Scene):
    """A law library where a law librarian can answer questions about case law."""

    def __init__(
        self,
        channel_id_legal: str,
        docs_per_dataset: int,
        enrichment_jsonl_file: Path,
        delay: float,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        milvus_uri: str,
        admin_channel_id: str,
        embedding_model_id: str = default_embedding_model_id,
        generator_model_id: str = default_generation_model_id,
        console: Optional[Console] = None,
    ) -> None:
        super().__init__()
        self.channel_id_legal = channel_id_legal
        self.docs_per_dataset = docs_per_dataset
        self.enrichment_jsonl_file = enrichment_jsonl_file
        self.delay = delay
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.milvus_uri = milvus_uri
        self.embedding_model_id = embedding_model_id
        self.generator_model_id = generator_model_id
        self.console = console

        self.doc_enrichments = DocumentEnrichments(
            self.docs_per_dataset, self.enrichment_jsonl_file, self.delay, self.console
        )

        self.case_law_knowledge_graph = CaseLawKnowledgeGraph(
            self.enrichment_jsonl_file,
            self.neo4j_uri,
            self.neo4j_username,
            self.neo4j_password,
            self.console,
        )

        self.entity_resolvers = EntityResolvers(
            self.milvus_uri,
            self.embedding_model_id,
            self.neo4j_uri,
            self.neo4j_username,
            self.neo4j_password,
            self.console,
        )

        self.driver = GraphDatabase.driver(
            neo4j_uri, auth=(neo4j_username, neo4j_password)
        )

        self.law_librarian = LawLibrarian(self.driver, milvus_uri, admin_channel_id)

    def props(self) -> list[Prop]:

        return [
            self.doc_enrichments,
            self.case_law_knowledge_graph,
            self.entity_resolvers,
        ]

    def characters(self) -> list[Character]:

        return [
            self.law_librarian,
        ]

    def places(
        self,
        channel_name_to_id: dict,
    ) -> dict[str, Character]:

        return {channel_name_to_id[self.channel_id_legal]: self.law_librarian}

    def curtain(self) -> None:
        self.driver.close()
        self.driver = None
