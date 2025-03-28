from typing import List, Optional

import logging
import json

from neo4j import Driver
from pathlib import Path
from rich.panel import Panel
from rich.prompt import Prompt
from stringcase import snakecase, lowercase
from langchain_core.documents.base import Document

from pydantic import BaseModel, Field
from pymilvus import MilvusClient

from proscenium.verbs.read import load_hugging_face_dataset
from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import raw_extraction_template
from proscenium.verbs.complete import complete_simple
from proscenium.scripts.graph_rag import extraction_system_prompt

from demo.config import default_model_id

###################################
# Knowledge Graph Schema
###################################

RELATION_JUDGE = "Judge"
RELATION_LEGAL_CITATION = "LegalCitation"
RELATION_COURT = "Court"

NODE_CASE = "Case"
NODE_ENTITY = "Entity"

###################################
# Retrieve Documens
###################################

hf_dataset_id = "free-law/nh"
hf_dataset_column = "text"
num_docs = 4

# Note: early version looked at only: doc.metadata["id"] in ['4440632', '4441078']


def retrieve_documents() -> List[Document]:

    docs = load_hugging_face_dataset(
        hf_dataset_id, page_content_column=hf_dataset_column
    )

    old_len = len(docs)
    docs = docs[:num_docs]
    logging.info(
        "using the first",
        num_docs,
        "documents of",
        old_len,
        "from HF dataset",
        hf_dataset_id,
    )

    for i, doc in enumerate(docs):
        doc.metadata["dataset_index"] = i

    return docs


def retrieve_document(id: str, driver: Driver) -> Optional[Document]:

    docs = load_hugging_face_dataset(
        hf_dataset_id, page_content_column=hf_dataset_column
    )

    with driver.session() as session:
        result = session.run("MATCH (n) RETURN n.dataset_index AS dataset_index")
        if len(result) == 0:
            logging.warning("No node n found in the graph")
            return None

        index = int(result[0]["dataset_index"])

        if 0 <= index < len(docs):
            return docs[index]
        else:
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
"""  # leaves out head_matter


def doc_as_rich(doc: Document):

    case_str = case_template.format_map(doc.metadata)

    return Panel(case_str, title=doc.metadata["name_abbreviation"])


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

    judges: list[str] = Field(
        description="A list of the judges mentioned in the text. For example: `Judge John Doe`"
    )
    # legal_citations: list[str] = Field(description = "A list of the legal citations in the text.  For example: `123 F.3d 456`")


def doc_enrichments(
    doc: Document, chunk_extracts: list[LegalOpinionChunkExtractions]
) -> list[dict]:

    citations: List[str] = get_citations(doc.page_content)

    # merge informaiion from all chunks
    judges = []
    for chunk_extract in chunk_extracts:
        judges.extend(chunk_extract.judges)

    return {
        "name": doc.metadata["name_abbreviation"],
        "dataset_index": doc.metadata["dataset_index"],
        "court": doc.metadata["court"],
        "citations": [c.matched_text() for c in citations],
        "judges": judges,
    }


chunk_extraction_template = partial_formatter.format(
    raw_extraction_template, extraction_description=LegalOpinionChunkExtractions.__doc__
)


###################################
# Knowledge Graph
###################################

entity_jsonl_file = Path("entities.jsonl")

neo4j_uri = "bolt://localhost:7687"  # os.environ["NEO4J_URI"]
neo4j_username = "neo4j"  # os.environ["NEO4J_USERNAME"]
neo4j_password = "password"  # os.environ["NEO4J_PASSWORD"]


def doc_enrichments_to_graph(tx, doc_enrichments: dict) -> None:

    case_name = doc_enrichments["name"]
    dataset_index = doc_enrichments["dataset_index"]

    triples = []
    triples.append((doc_enrichments["court"], RELATION_COURT, case_name))
    for judge in doc_enrichments["judges"]:
        triples.append((judge, RELATION_JUDGE, case_name))
    for citation in doc_enrichments["citations"]:
        triples.append((citation, RELATION_LEGAL_CITATION, case_name))

    for subject, predicate, object in triples:
        query = (
            "MERGE (e:Entity {name: $entity}) "
            "MERGE (c:Case {name: $case, dataset_index: $dataset_index}) "
            "MERGE (e)-[r:%s]->(c)"
        ) % snakecase(lowercase(predicate))
        tx.run(
            query,
            entity=subject,
            case=case_name,
            dataset_index=dataset_index,
        )


###################################
# user_question
###################################


def user_question() -> str:

    question = Prompt.ask(
        f"What is your question about {hf_dataset_id}?",
        default="How has Judge Kenison used Ballou v. Ballou to rule on cases?",
    )

    return question


###################################
# query_extract
###################################

default_query_extraction_model_id = default_model_id


class QueryExtractions(BaseModel):
    """
    The extracted judges from the user query.
    """

    judges: list[str] = Field(
        description="A list of the judges mentioned in the query. For example: `Judge John Doe`"
    )
    # legal_citations: list[str] = Field(description = "A list of the legal citations in the query.  For example: `123 F.3d 456`")


query_extraction_template = partial_formatter.format(
    raw_extraction_template, extraction_description=QueryExtractions.__doc__
)


def query_extract(query: str, query_extraction_model_id: str) -> QueryExtractions:

    extract = complete_simple(
        query_extraction_model_id,
        extraction_system_prompt,
        query_extraction_template.format(text=query),
        response_format={
            "type": "json_object",
            "schema": QueryExtractions.model_json_schema(),
        },
        rich_output=True,
    )

    logging.info("query_extract: extract = <<<%s>>>", extract)

    try:

        qe_json = json.loads(extract)

        return QueryExtractions(**qe_json)

    except Exception as e:

        logging.error("query_extract: Exception: %s", e)

    finally:
        return None


###################################
# extract_to_context
###################################


class LegalQueryContext(BaseModel):
    """
    Context for generating answer in response to legal question.
    """

    doc: str = Field(
        description="The retrieved document text that is relevant to the question."
    )
    query: str = Field(description="The original question asked by the user.")
    # legal_citations: list[str] = Field(description = "A list of the legal citations in the text.  For example: `123 F.3d 456`")


embedding_model_id = "all-MiniLM-L6-v2"

milvus_uri = "file:/grag-milvus.db"


def extract_to_context(
    qe: QueryExtractions, query: str, driver: Driver, vector_db_client: MilvusClient
) -> LegalQueryContext:

    subject_predicate_constraints = []
    for judge in qe.judges:
        subject_predicate_constraints.append((judge, RELATION_JUDGE))
    for citation in get_citations(query):
        subject_predicate_constraints.append((citation, RELATION_LEGAL_CITATION))

    query = ""
    for i, (subject, predicate) in enumerate(subject_predicate_constraints):
        predicate_lc = snakecase(lowercase(predicate.replace("/", "_")))
        query += (
            f"MATCH (e{str(i)}:Entity {{name: '{subject}'}})-[:{predicate_lc}]->(c)\n"
        )
    query += "RETURN c.name AS name"

    object_names = []
    with driver.session() as session:
        result = session.run(query)
        object_names.extend([record["name"] for record in result])

    print("Objects with names:", object_names, "are matches")

    doc = retrieve_document(object_names[0])

    context = LegalQueryContext(
        doc=doc.page_content,
        query=query,
    )

    return context


###################################
# context_to_prompts
###################################

generation_system_prompt = "You are a helpful law librarian"

graphrag_prompt_template = """
Answer the question using the following text from one case:

{document_text}

Question: {question}
"""


def context_to_prompts(context: LegalQueryContext) -> tuple[str, str]:

    user_prompt = graphrag_prompt_template.format(
        document_text=context.doc, question=context.query
    )

    return generation_system_prompt, user_prompt


###################################
# generation
###################################

default_generation_model_id = default_model_id
