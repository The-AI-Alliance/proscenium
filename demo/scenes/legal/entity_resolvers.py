from typing import Optional
import logging

from rich.console import Console
from neo4j import GraphDatabase

from proscenium.patterns.entity_resolver import load_entity_resolver
from proscenium.patterns.entity_resolver import vector_db
from proscenium.patterns.entity_resolver import Resolver

from proscenium.core import Prop

default_embedding_model_id = "all-MiniLM-L6-v2"

log = logging.getLogger(__name__)

case_resolver = Resolver(
    "MATCH (cr:CaseRef) RETURN cr.text AS text",
    "text",
    "resolve_caserefs",
)

judge_resolver = Resolver(
    "MATCH (jr:JudgeRef) RETURN jr.text AS text",
    "text",
    "resolve_judgerefs",
)


class EntityResolvers(Prop):
    """
    An entity resolver for resolving case and judge references in legal documents."""

    def __init__(
        self,
        milvus_uri: str,
        embedding_model_id: str,
        neo4j_uri: str,
        neo4j_username: str,
        neo4j_password: str,
        console: Optional[Console] = None,
    ) -> None:
        super().__init__(console)
        self.milvus_uri = milvus_uri
        self.embedding_model_id = embedding_model_id
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password

        self.resolvers = [case_resolver, judge_resolver]

    def already_built(self) -> bool:
        client = vector_db(self.milvus_uri)
        collections = client.list_collections()
        try:
            for resolver in self.resolvers:
                collection_name = resolver.collection_name
                if collection_name not in collections:
                    return False
                # row_count = client.get_collection_stats(collection_name)["row_count"]
        finally:
            client.close()

        return True

    def build(self) -> None:

        driver = GraphDatabase.driver(
            self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password)
        )

        try:
            load_entity_resolver(
                driver,
                self.resolvers,
                self.embedding_model_id,
                self.milvus_uri,
                console=self.console,
            )
        finally:
            driver.close()
