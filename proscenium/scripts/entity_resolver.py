from typing import List

from rich import print

from langchain_core.documents.base import Document
from neo4j import Driver

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.vector_database import create_vector_db
from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.display.milvus import collection_panel


class EntityResolver:

    def __init__(self, collection_name: str, cypher: str, field_name: str):
        self.collection_name = collection_name
        self.cypher = cypher
        self.field_name = field_name


def load_entity_resolver(
    driver: Driver,
    resolvers: list[EntityResolver],
    milvus_uri: str,
    embedding_model_id: str,
) -> None:

    embedding_fn = embedding_function(embedding_model_id)
    print("Embedding model", embedding_model_id)

    for resolver in resolvers:

        vector_db_client = create_vector_db(
            milvus_uri, embedding_fn, resolver.collection_name, overwrite=True
        )
        print("Vector db stored at", milvus_uri)

        values = []
        with driver.session() as session:
            result = session.run(resolver.cypher)
            new_values = [Document(record[resolver.field_name]) for record in result]
            values.extend(new_values)

        print("Loading entity resolver into vector db", resolver.collection_name)

        info = add_chunks_to_vector_db(
            vector_db_client, embedding_fn, values, resolver.collection_name
        )
        print(info["insert_count"], "chunks inserted")
        print(collection_panel(vector_db_client, resolver.collection_name))

        vector_db_client.close()


def find_matching_objects(
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    question_triples: List[tuple[str, str, str]],
) -> List[tuple[str, str]]:

    subject_predicate_pairs = []
    for triple in question_triples:
        print("Finding entity matches for", triple[0], "(", triple[1], ")")
        subject, predicate, obj = triple
        # TODO collection_name = "resolver_" + field_name
        collection_name = "chunks"  # TODO
        # TODO apply distance threshold
        hits = closest_chunks(
            vector_db_client, embedding_fn, subject, collection_name, k=5
        )
        for match in [head["entity"]["text"] for head in hits[:1]]:
            print("   match:", match)
            subject_predicate_pairs.append((match, predicate))
    # Note: the above block loses the tie-back link from the match to the original triple

    return subject_predicate_pairs
