from typing import Optional, Callable, List

import logging

from rich.console import Console
from neo4j import GraphDatabase

from proscenium.scripts.entity_resolver import load_entity_resolver
from proscenium.scripts.entity_resolver import vector_db
from proscenium.scripts.entity_resolver import Resolver

from demo.domains.legal.entity_resolvers import resolvers

log = logging.getLogger(__name__)


def make_entity_resolver_loader(
    milvus_uri: str,
    embedding_model_id: str,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    console: Optional[Console] = None,
) -> Callable[[bool], None]:

    def already_built(milvus_uri: str, resolvers: List[Resolver]):
        client = vector_db(milvus_uri, overwrite=False)
        collections = client.list_collections()
        try:
            for resolver in resolvers:
                collection_name = resolver.collection_name
                if collection_name not in collections:
                    return False
                # row_count = client.get_collection_stats(collection_name)["row_count"]
        finally:
            client.close()

        return True

    def load(force: bool = False):

        if force or already_built(milvus_uri, resolvers):
            log.info("Entity resolver already built.")
            return

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

        load_entity_resolver(
            driver,
            resolvers,
            embedding_model_id,
            milvus_uri,
            console=console,
        )

        driver.close()

    return load
