
from typing import List

from stringcase import snakecase, lowercase

from langchain_core.documents.base import Document
from neo4j import Driver
from pymilvus import MilvusClient
from pymilvus import model

from rich import print

from proscenium.parse import PartialFormatter
from proscenium.parse import raw_extraction_template
from proscenium.parse import get_triples_from_extract
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.complete import complete_simple
from proscenium.read import load_hugging_face_dataset
from proscenium.vector_database import closest_chunks
from proscenium.display import display_chunk_hits

# Problem-specific configuration:
import example.graph_rag.config as config
import example.graph_rag.util as util

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in config.predicates.items()]))

extraction_system_prompt = "You are an entity extractor"

#def extract_triples_from_atomic_doc(
#    chunk: Document,
#    object: str) -> List[tuple[str, str, str]]:
#
#    extract = complete_simple(
#        config.model_id,
#        extraction_system_prompt,
#        extraction_template.format(text = chunk.page_content))
#
#    new_triples = get_triples_from_extract(extract, object, config.predicates)
#
#    return new_triples


def process_document(
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
            extraction_template.format(text = chunk.page_content))

        new_triples = get_triples_from_extract(extract, object, config.predicates)

        print("Found", len(new_triples), "triples in chunk", i+1, "of", len(chunks))

        doc_triples.extend(new_triples)

    return doc_triples

def case_text_for_name(name: str) -> str:

    # TODO avoid this by indexing the case text elsewhere (eg the graph)

    documents = load_hugging_face_dataset(
        config.hf_dataset_id,
        page_content_column = config.hf_dataset_column)
    print("Document Count:", len(documents))

    print("Truncating to", config.num_docs)
    documents = documents[:config.num_docs]

    for doc in documents:
        if doc.metadata["name_abbreviation"] == name:
            return doc.page_content

def match_entity(
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    name: str):

    """Match entities by embedding vector distance."""

    # TODO take a distance threshold as an argument

    hits = closest_chunks(vector_db_client, embedding_fn, name, k=5)
    # display_chunk_hits(hits)

    if len(hits) > 0:
        # TODO confirm that 0th element is the closest match
        hit = hits[0]
        return hit['entity']['text']
    else:
        return None

def query_for_cases(driver: Driver, entity_role_pairs):
    with driver.session() as session:
        query = ""
        for i, (entity, role) in enumerate(entity_role_pairs):
            relationship = snakecase(lowercase(role.replace('/', '_')))
            query += f"MATCH (e{str(i)}:Entity {{name: '{entity}'}})-[:{relationship}]->(c)\n"
        query += "RETURN c.name AS name"
        print(query)
        result = session.run(query)
        cases = []
        print("Cases:")
        for record in result:
            cases.append(record["name"])
            print(record["name"])
        return cases

query_template = """
Answer the question using the following text from one case:

{case_text}

Question: {question}
"""

def graphrag_prompt(case_text: str, question: str) -> str:

    query = query_template.format(
        case_text = case_text,
        question = question)

    return query