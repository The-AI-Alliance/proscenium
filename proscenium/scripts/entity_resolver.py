from typing import Optional
from rich import print

from langchain_core.documents.base import Document
from neo4j import Driver

from pymilvus import MilvusClient

from proscenium.verbs.vector_database import vector_db
from proscenium.verbs.vector_database import create_collection
from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.display.milvus import collection_panel


class Resolver:

    def __init__(
        self,
        cypher: str,
        field_name: str,
        collection_name: str,
        embedding_model_id: str,
    ):
        self.cypher = cypher
        self.field_name = field_name
        self.collection_name = collection_name
        self.embedding_model_id = embedding_model_id


def load_entity_resolver(
    driver: Driver,
    resolvers: list[Resolver],
    milvus_uri: str,
) -> None:

    vector_db_client = vector_db(milvus_uri, overwrite=True)
    print("Vector db stored at", milvus_uri)

    for resolver in resolvers:

        embedding_fn = embedding_function(resolver.embedding_model_id)
        print("Embedding model", resolver.embedding_model_id)

        values = []
        with driver.session() as session:
            result = session.run(resolver.cypher)
            new_values = [Document(record[resolver.field_name]) for record in result]
            values.extend(new_values)

        print("Loading entity resolver into vector db", resolver.collection_name)
        create_collection(
            vector_db_client, embedding_fn, resolver.collection_name, overwrite=True
        )
        info = add_chunks_to_vector_db(
            vector_db_client, embedding_fn, values, resolver.collection_name
        )
        print(info["insert_count"], "chunks inserted")
        print(collection_panel(vector_db_client, resolver.collection_name))

    vector_db_client.close()


def find_matching_objects(
    vector_db_client: MilvusClient,
    approximate: str,
    resolver: Resolver,
) -> Optional[str]:

    print("Loading collection", resolver.collection_name)
    vector_db_client.load_collection(resolver.collection_name)

    print("Finding entity matches for", approximate, "using", resolver.collection_name)

    hits = closest_chunks(
        vector_db_client,
        resolver.embedding_fn,
        approximate,
        resolver.collection_name,
        k=5,
    )
    # TODO apply distance threshold
    for match in [head["entity"]["text"] for head in hits[:1]]:
        print("Closest match:", match)
        return match

    print("No match found")
    return None
