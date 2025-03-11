
from typing import List

from stringcase import snakecase, lowercase

from langchain_core.documents.base import Document
from neo4j import Driver

from rich import print
from rich.panel import Panel

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.parse import PartialFormatter
from proscenium.parse import raw_extraction_template
from proscenium.parse import get_triples_from_extract
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.complete import complete_simple
from proscenium.read import load_hugging_face_dataset
from proscenium.vector_database import closest_chunks

# Problem-specific configuration:
import example.graph_rag.config as config
import example.graph_rag.util as util

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in config.predicates.items()]))

extraction_system_prompt = "You are an entity extractor"

def extract_triples_from_document(
    doc: Document
    ) -> List[tuple[str, str, str]]:

    config.doc_display(doc)

    doc_triples = []

    direct_triples = config.doc_direct_triples(doc)
    doc_triples.extend(direct_triples)

    object = config.doc_as_object(doc)

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        extract = complete_simple(
            config.model_id,
            util.extraction_system_prompt,
            extraction_template.format(text = chunk.page_content),
            rich_output = True)

        new_triples = get_triples_from_extract(extract, object, config.predicates)

        print("Found", len(new_triples), "triples in chunk", i+1, "of", len(chunks))

        doc_triples.extend(new_triples)

    return doc_triples

def full_doc_by_id(name: str) -> Document:

    # TODO avoid this by storing docs elsewhere (eg the graph)
    documents = load_hugging_face_dataset(
        config.hf_dataset_id,
        page_content_column = config.hf_dataset_column)

    print("Searching the first", config.num_docs,
        " documents of", len(documents),
        "in", config.hf_dataset_id, "column", config.hf_dataset_column)

    documents = documents[:config.num_docs]

    for doc in documents:
        object = config.doc_as_object(doc)
        if object == name:
            return doc

def query_for_objects(
    driver: Driver,
    subject_predicate_constraints: List[tuple[str, str]]
    ) -> List[str]:
    with driver.session() as session:
        query = ""
        for i, (subject, predicate) in enumerate(subject_predicate_constraints):
            predicate_lc = snakecase(lowercase(predicate.replace('/', '_')))
            query += f"MATCH (e{str(i)}:Entity {{name: '{subject}'}})-[:{predicate_lc}]->(c)\n"
        query += "RETURN c.name AS name"
        print(Panel(query, title="Cypher Query"))
        result = session.run(query)
        objects = []
        print("   Result:")
        for record in result:
            objects.append(record["name"])
            print(record["name"])
        return objects


def find_matching_objects(
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    question_triples: List[tuple[str, str, str]]
    ) -> List[tuple[str, str]]:

    subject_predicate_pairs = []
    for triple in question_triples:
        print("Finding entity matches for", triple[0], "(", triple[1], ")")
        subject, predicate, object = triple
        # TODO apply distance threshold
        hits = closest_chunks(vector_db_client, embedding_fn, subject, k=5)
        for match in [head['entity']['text'] for head in hits[:1]]:
            print("   match:", match)
            subject_predicate_pairs.append((match, predicate))
    # Note: the above block loses the tie-back link from the match to the original triple

    return subject_predicate_pairs
