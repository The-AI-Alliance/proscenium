
from typing import List, Optional

import logging
import json

from pathlib import Path
from rich.panel import Panel
from rich.prompt import Prompt
from stringcase import snakecase, lowercase
from langchain_core.documents.base import Document

from pydantic import BaseModel, Field

from proscenium.typer.config import default_model_id
from proscenium.verbs.read import load_hugging_face_dataset
from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import raw_extraction_template
from proscenium.verbs.complete import complete_simple

from proscenium.scripts.graph_rag import extraction_system_prompt

from proscenium.typer.config import default_model_id

###################################
# Knowledge Graph Schema
###################################

RELATION_JUDGE = "Judge"
RELATION_LEGAL_CITATION = "LegalCitation"
RELATION_COURT = "Court"

###################################
# Retrieve Documens
###################################

hf_dataset_id = "free-law/nh"
hf_dataset_column = "text"
num_docs = 4

# Note: early version looked at only: doc.metadata["id"] in ['4440632', '4441078']

def retrieve_documents() -> List[Document]:

    docs = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)

    old_len = len(docs)
    docs = docs[:num_docs]
    logging.info("using the first", num_docs, "documents of", old_len, "from HF dataset", hf_dataset_id)

    return docs

def doc_as_object(doc: Document) -> str:
    return doc.metadata['name_abbreviation']

# TODO index the docs after the first `retrieve_documents` call,
# so that `retrieve_document` is efficient

def retrieve_document(id: str) -> Optional[Document]:

    docs = retrieve_documents()
    for doc in docs:
        if doc_as_object(doc) == id:
            return doc

    return None

###################################
# Data display
###################################

case_template = """
[u]{name}[/u]
{reporter}, Volume {volume} pages {first_page}-{last_page}
Court: {court}
Decision Date: {decision_date}
Citations: {citations}

Docket Number: {docket_number}
Jurisdiction: {jurisdiction}
Judges: {judges}
Parties: {parties}

Word Count: {word_count}, Character Count: {char_count}
Last Updated: {last_updated}, Provenance: {provenance}
Id: {id}
""" # leaves out head_matter

def doc_as_rich(doc: Document):
    
    case_str = case_template.format_map(doc.metadata)

    return Panel(case_str, title=doc.metadata['name_abbreviation'])

###################################
# Chunk Extraction
###################################

# `judge` is not well captured in many of these documents,
# so we will extract it from the text

from eyecite import get_citations

default_chunk_extraction_model_id = default_model_id

class LegalOpinionChunkExtractions(BaseModel):
    """
    The extracted judges from a chunk of a legal opinion.
    """
    judges: list[str] = Field(description = "A list of the judges mentioned in the text. For example: `Judge John Doe`")
    # legal_citations: list[str] = Field(description = "A list of the legal citations in the text.  For example: `123 F.3d 456`")

chunk_extraction_data_model = LegalOpinionChunkExtractions

def doc_direct_triples(doc: Document) -> list[tuple[str, str, str]]:

    obj: str = doc_as_object(doc)

    triples = []

    subject = doc.metadata["court"]
    relation = RELATION_COURT
    triples.append((subject, relation, obj))

    citations: List[str] = get_citations(doc.page_content)

    relation = RELATION_LEGAL_CITATION
    for citation in citations:
        # TODO there are several fields in citation object that should be
        # stored in the graph
        subject: str = citation.matched_text()
        triples.append((subject, relation, obj))

    return triples

chunk_extraction_template = partial_formatter.format(
    raw_extraction_template,
    extraction_description = LegalOpinionChunkExtractions.__doc__
    )

def get_triples_from_chunk(
    chunk_extraction_model_id: str,
    chunk: Document,
    doc: Document,
    ) -> List[tuple[str, str, str]]:

    obj: str = doc_as_object(doc)

    loce_str = complete_simple(
        chunk_extraction_model_id,
        extraction_system_prompt,
        chunk_extraction_template.format(text = chunk.page_content),
        response_format = {
            "type": "json_object",
            "schema": LegalOpinionChunkExtractions.model_json_schema(),
        },
        rich_output = True)

    logging.info("get_triples_from_chunk_extract: loce_str = <<<%s>>>", loce_str)

    triples = []
    try:
        loce_py = json.loads(loce_str)
        loce = LegalOpinionChunkExtractions(**loce_py)
        for judge in loce.judges:
            triple = (judge.strip(), RELATION_JUDGE, obj)
            triples.append(triple)
        #for citation in loce.legal_citations:
        #    triple = (citation.strip(), RELATION_LEGAL_CITATION, obj)
        #    triples.append(triple)
    except Exception as e:
        logging.error("get_triples_from_chunk_extract: Exception: %s", e)
    finally:
        return triples


###################################
# Knowledge Graph
###################################

entity_csv_file = Path("entities.csv")

neo4j_uri = "bolt://localhost:7687" # os.environ["NEO4J_URI"]
neo4j_username = "neo4j" # os.environ["NEO4J_USERNAME"]
neo4j_password = "password" # os.environ["NEO4J_PASSWORD"]

def add_triple(tx, entity: str, role: str, case: str) -> None:
    query = (
        "MERGE (e:Entity {name: $entity}) "
        "MERGE (c:Case {name: $case}) "
        "MERGE (e)-[r:%s]->(c)"
    ) % snakecase(lowercase(role.replace('/', '_')))
    tx.run(query, entity=entity, case=case)

###################################
# Entity Resolution
###################################

embedding_model_id = "all-MiniLM-L6-v2"

milvus_uri = "file:/grag-milvus.db"

###################################
# Querying
###################################

def get_user_question() -> str:

    question = Prompt.ask(
        f"What is your question about {hf_dataset_id}?",
        default = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"
        )

    return question

###################################
# Query Extraction
###################################

query_extraction_model_id = default_model_id

class QueryExtractions(BaseModel):
    """
    The extracted judges from the user query.
    """
    judges: list[str] = Field(description = "A list of the judges mentioned in the query. For example: `Judge John Doe`")
    # legal_citations: list[str] = Field(description = "A list of the legal citations in the query.  For example: `123 F.3d 456`")

query_extraction_data_model = QueryExtractions

def query_direct_triples(query: str) -> list[tuple[str, str, str]]:

    object = ""

    triples = []
    relation = RELATION_LEGAL_CITATION
    for citation in get_citations(query):
        subject = citation.strip()
        triples.append((subject, relation, object))

    return triples

query_extraction_template = partial_formatter.format(
    raw_extraction_template,
    extraction_description = QueryExtractions.__doc__
    )

def get_triples_from_query_extract(
    qe_str: str,
    object: str,
    ) -> List[tuple[str, str, str]]:

    logging.info("get_triples_from_query_extract: qe_str = <<<%s>>>", qe_str)

    triples = []
    try:
        qe_json = json.loads(qe_str)
        qe = QueryExtractions(**qe_json)

        relation = RELATION_JUDGE
        for judge in qe.judges:
            subject = judge.strip()
            triples.append((subject, relation, object))

        #relation = RELATION_LEGAL_CITATION
        #for citation in qe.legal_citations:
        #    subject = citation.strip()
        #    triples.append((subject, relation, object))

    except Exception as e:
        logging.error("get_triples_from_query_extract: Exception: %s", e)
    finally:
        return triples

###################################
# Query Search
###################################

def matching_objects_query(
    subject_predicate_constraints: List[tuple[str, str]]) -> str:
    query = ""
    for i, (subject, predicate) in enumerate(subject_predicate_constraints):
        predicate_lc = snakecase(lowercase(predicate.replace('/', '_')))
        query += f"MATCH (e{str(i)}:Entity {{name: '{subject}'}})-[:{predicate_lc}]->(c)\n"
    query += "RETURN c.name AS name"

    return query

###################################
# Response Generation
####################################

default_generation_model_id = default_model_id

system_prompt = "You are a helpful law librarian"

graphrag_prompt_template = """
Answer the question using the following text from one case:

{document_text}

Question: {question}
"""
