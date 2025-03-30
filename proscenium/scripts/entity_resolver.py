from typing import List

from rich import print

from langchain_core.documents.base import Document
from neo4j import Driver

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.display.milvus import collection_panel


def load_entity_resolver(
    driver: Driver,
    cypher: str,
    field_name: str,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
) -> None:

    values = []
    with driver.session() as session:
        result = session.run(cypher)
        new_values = [Document(record[field_name]) for record in result]
        values.extend(new_values)

    # TODO collection_name = "resolver_" + field_name
    collection_name = "chunks"  # TODO
    print("Loading entity resolver into vector db", collection_name)

    info = add_chunks_to_vector_db(
        vector_db_client, embedding_fn, values, collection_name
    )
    print(info["insert_count"], "chunks inserted")
    print(collection_panel(vector_db_client, collection_name))


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
