
from typing import List

from stringcase import snakecase, lowercase

from langchain_core.documents.base import Document
from neo4j import Driver

from rich import print

from proscenium.parse import PartialFormatter
from proscenium.parse import raw_extraction_template
from proscenium.parse import get_triples_from_extract
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.complete import complete_simple
from proscenium.read import load_hugging_face_dataset

# Problem-specific configuration:
import example.graph_rag.config as config
import example.graph_rag.util as util

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in config.predicates.items()]))

extraction_system_prompt = "You are an entity extractor"

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
        print(query)
        result = session.run(query)
        objects = []
        print("   Result:")
        for record in result:
            objects.append(record["name"])
            print(record["name"])
        return objects

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