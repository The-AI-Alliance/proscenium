from typing import Optional, Callable

from rich.console import Console
from neo4j import GraphDatabase

from proscenium.scripts.entity_resolver import load_entity_resolver

from demo.domains.legal.entity_resolvers import resolvers


def make_entity_resolver_loader(
    milvus_uri: str,
    embedding_model_id: str,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    console: Optional[Console] = None,
) -> Callable[[bool], None]:

    def load(force: bool = False):

        # TODO check if the resolvers are already loaded

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
