
from typing import List

import logging
import json

from pathlib import Path
from rich.panel import Panel
from rich.prompt import Prompt
from stringcase import snakecase, lowercase
from langchain_core.documents.base import Document

from pydantic import BaseModel, Field

from proscenium.typer.config import default_model_id
from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import raw_extraction_template

from proscenium.typer.config import default_model_id

###################################
# Input data
###################################

hf_dataset_id = "free-law/nh"
hf_dataset_column = "text"
num_docs = 4
# initial version looked at only: doc.metadata["id"] in ['4440632', '4441078']

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
# Extraction
###################################

chunk_extraction_model_id = default_model_id

class LegalOpinionChunkExtractions(BaseModel):
    """
    The extracted judges and legal citations from a legal opinion chunk.
    """
    judges: list[str] = Field(description = "A list of the judges mentioned in the text. For example: `Judge John Doe`")
    legal_citations: list[str] = Field(description = "A list of the legal citations in the text.  For example: `123 F.3d 456`")

chunk_extraction_data_model = LegalOpinionChunkExtractions

def doc_as_object(doc: Document) -> str:
    return doc.metadata['name_abbreviation']

def doc_direct_triples(doc: Document) -> list[tuple[str, str, str]]:
    object: str = doc_as_object(doc)
    return [(doc.metadata["court"], 'Court', object)]

# For the purpose of this recipe, note that the `judge`
# is not well captured in many of these documents;
# we will be extracting it from the case law text.

chunk_extraction_template = partial_formatter.format(
    raw_extraction_template,
    extraction_description = LegalOpinionChunkExtractions.__doc__
    )

def get_triples_from_chunk_extract(
    loce_str: str,
    object: str,
    ) -> List[tuple[str, str, str]]:

    logging.info("get_triples_from_extract: leo_str = <<<%s>>>", loce_str)

    loce_json = json.loads(loce_str)
    loce = LegalOpinionChunkExtractions(**loce_json)

    triples = []
    for judge in loce.judges:
        triple = (judge.strip(), 'Judge', object)
        triples.append(triple)
    for citation in loce.legal_citations:
        triple = (citation.strip(), 'LegalCitation', object)
        triples.append(triple)
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
# Query Handling
###################################

def get_user_question() -> str:

    question = Prompt.ask(
        f"What is your question about {hf_dataset_id}?",
        default = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"
        )

    return question


query_extraction_model_id = default_model_id

class QueryExtractions(BaseModel):
    """
    The extracted judges and legal citations from user query.
    """
    judges: list[str] = Field(description = "A list of the judges mentioned in the query. For example: `Judge John Doe`")
    legal_citations: list[str] = Field(description = "A list of the legal citations in the query.  For example: `123 F.3d 456`")

query_extraction_data_model = QueryExtractions

def query_direct_triples(query: str) -> list[tuple[str, str, str]]:
    return []

query_extraction_template = partial_formatter.format(
    raw_extraction_template,
    extraction_description = QueryExtractions.__doc__
    )

def get_triples_from_query_extract(
    qe_str: str,
    object: str,
    ) -> List[tuple[str, str, str]]:

    logging.info("get_triples_from_query_extract: qe_str = <<<%s>>>", qe_str)

    qe_json = json.loads(qe_str)
    qe = QueryExtractions(**qe_json)

    triples = []
    for judge in qe.judges:
        triple = (judge.strip(), 'Judge', object)
        triples.append(triple)
    for citation in qe.legal_citations:
        triple = (citation.strip(), 'LegalCitation', object)
        triples.append(triple)
    return triples


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

generation_model_id = default_model_id

system_prompt = "You are a helpful law librarian"

graphrag_prompt_template = """
Answer the question using the following text from one case:

{document_text}

Question: {question}
"""
