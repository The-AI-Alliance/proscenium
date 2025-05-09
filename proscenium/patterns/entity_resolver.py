from typing import Optional
import logging

from rich.console import Console
from langchain_core.documents.base import Document
from neo4j import Driver

from pymilvus import MilvusClient

from proscenium.verbs.vector_database import vector_db
from proscenium.verbs.vector_database import create_collection
from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.display.milvus import collection_panel

log = logging.getLogger(__name__)


class Resolver:

    def __init__(
        self,
        cypher: str,
        field_name: str,
        collection_name: str,
    ):
        self.cypher = cypher
        self.field_name = field_name
        self.collection_name = collection_name


def load_entity_resolver(
    driver: Driver,
    resolvers: list[Resolver],
    embedding_model_id: str,
    milvus_uri: str,
    console: Optional[Console] = None,
) -> None:

    vector_db_client = vector_db(milvus_uri)
    log.info("Vector db stored at %s", milvus_uri)

    embedding_fn = embedding_function(embedding_model_id)
    log.info("Embedding model %s", embedding_model_id)

    for resolver in resolvers:

        values = []
        with driver.session() as session:
            result = session.run(resolver.cypher)
            new_values = [Document(record[resolver.field_name]) for record in result]
            values.extend(new_values)

        log.info("Loading entity resolver into vector db %s", resolver.collection_name)
        create_collection(vector_db_client, embedding_fn, resolver.collection_name)

        info = add_chunks_to_vector_db(
            vector_db_client, embedding_fn, values, resolver.collection_name
        )
        log.info("%s chunks inserted ", info["insert_count"])

        if console is not None:
            console.print(collection_panel(vector_db_client, resolver.collection_name))

    vector_db_client.close()


def find_matching_objects(
    vector_db_client: MilvusClient,
    approximate: str,
    resolver: Resolver,
) -> Optional[str]:

    log.info("Loading collection", resolver.collection_name)
    vector_db_client.load_collection(resolver.collection_name)

    log.info(
        "Finding entity matches for", approximate, "using", resolver.collection_name
    )

    hits = closest_chunks(
        vector_db_client,
        resolver.embedding_fn,
        approximate,
        resolver.collection_name,
        k=5,
    )
    # TODO apply distance threshold
    for match in [head["entity"]["text"] for head in hits[:1]]:
        log.info("Closest match:", match)
        return match

    log.info("No match found")
    return None
