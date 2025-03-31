from typing import List, Optional

import logging
import json

from neo4j import Driver
from rich import print
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from stringcase import snakecase, lowercase
from langchain_core.documents.base import Document

from pydantic import BaseModel, Field

from proscenium.verbs.read import load_hugging_face_dataset
from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import extraction_system_prompt
from proscenium.verbs.extract import raw_extraction_template
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.entity_resolver import EntityResolver
from proscenium.scripts.entity_resolver import find_matching_objects

from demo.config import default_model_id

###################################
# Knowledge Graph Schema
###################################

RELATION_JUDGE = "Judge"
RELATION_LEGAL_CITATION = "LegalCitation"
RELATION_COURT = "Court"

###################################
# Retrieve Documents
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


class LegalOpinionEnrichments(BaseModel):
    """
    Enrichments for a legal opinion document.
    """

    name: str = Field(description="opinion identifier; name abbreviation")
    dataset_index: int = Field(description="index of the document in the dataset")
    court: str = Field(description="name of the court")
    judges: list[str] = Field(
        description="A list of the judges mentioned in the text. For example: `Judge John Doe`"
    )
    citations: list[str] = Field(
        description="A list of the legal citations in the text.  For example: `123 F.3d 456`"
    )


def doc_enrichments(
    doc: Document, chunk_extracts: list[LegalOpinionChunkExtractions]
) -> LegalOpinionEnrichments:

    citations: List[str] = get_citations(doc.page_content)

    # merge informaiion from all chunks
    judges = []
    for chunk_extract in chunk_extracts:
        judges.extend(chunk_extract.judges)

    enrichments = LegalOpinionEnrichments(
        name=doc.metadata["name_abbreviation"],
        dataset_index=int(doc.metadata["dataset_index"]),
        court=doc.metadata["court"],
        citations=[c.matched_text() for c in citations],
        judges=judges,
    )

    return enrichments


chunk_extraction_template = partial_formatter.format(
    raw_extraction_template, extraction_description=LegalOpinionChunkExtractions.__doc__
)


###################################
# Knowledge Graph
###################################


def doc_enrichments_to_graph(tx, enrichments: LegalOpinionEnrichments) -> None:

    case_name = enrichments.name
    dataset_index = enrichments.dataset_index

    tx.run(
        "MERGE (c:Case {name: $case, dataset_index: $dataset_index})",
        case=case_name,
        dataset_index=dataset_index,
    )

    for judge in enrichments.judges:
        tx.run(
            "MERGE (j:Judge {name: $judge})\n"
            + "MERGE (c:Case {name: $case})-[:mentions]->(j)",
            judge=judge,
            case=case_name,
        )

    for citation in enrichments.citations:
        # TODO resolve citation
        tx.run(
            "MERGE (c:Case {name: $citation})\n"
            + "MERGE (o:Case {name: $case})-[:cites]->(c)",
            case=case_name,
            citation=citation,
        )


def show_knowledge_graph(driver: Driver):

    with driver.session() as session:

        result = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel"
        )  # all relationships
        relations = [record["rel"] for record in result]
        unique_relations = list(set(relations))
        table = Table(title="Relationship Types", show_lines=False)
        table.add_column("Relationship Type", justify="left")
        for r in unique_relations:
            table.add_row(r)
        print(table)

        result = session.run(
            "MATCH (n) RETURN n.name AS name, labels(n) as label"
        )  # all nodes
        table = Table(title="Nodes", show_lines=False)
        table.add_column("Name", justify="left")
        table.add_column("Labels", justify="left")
        for record in result:
            table.add_row(record["name"], ", ".join(record["label"]))
        print(table)

        for r in unique_relations:
            cypher = f"MATCH (s)-[:{r}]->(o) RETURN s.name, o.name"
            result = session.run(cypher)
            table = Table(title=f"Relation: {r}", show_lines=False)
            table.add_column("Subject Name", justify="left")
            table.add_column("Object Name", justify="left")
            for record in result:
                table.add_row(record["s.name"], record["o.name"])
            print(table)


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
    # citations: list[str] = Field(description = "A list of the legal citations in the query.  For example: `123 F.3d 456`")


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

embedding_model_id = "all-MiniLM-L6-v2"

citation_resolver = EntityResolver(
    "MATCH (c:Case) RETURN c.name AS name",
    "name",
    "resolve_citations",  # TODO change
    embedding_model_id,
)

judge_resolver = EntityResolver(
    "MATCH (j:Judge) RETURN j.name AS name",
    "name",
    "resolve_judges",
    embedding_model_id,
)

resolvers = [
    citation_resolver,
    # TODO judge_resolver
]


class LegalQueryContext(BaseModel):
    """
    Context for generating answer in response to legal question.
    """

    doc: str = Field(
        description="The retrieved document text that is relevant to the question."
    )
    query: str = Field(description="The original question asked by the user.")
    # citations: list[str] = Field(description = "A list of the legal citations in the text.  For example: `123 F.3d 456`")


def extract_to_context(
    qe: QueryExtractions, query: str, driver: Driver, milvus_uri: str
) -> LegalQueryContext:

    vector_db_client = vector_db(milvus_uri)

    query = ""
    # TODO
    # for i, judge in enumerate(qe.judges):
    #     query += (
    #         f"MATCH (judge{str(i)}:Judge {{name: '{judge}'}})-[:mentioned_in]->(c)\n"
    #     )
    for citation in get_citations(query):
        citation_match = find_matching_objects(
            vector_db_client, citation, citation_resolver
        )
        query += f"MATCH (o:Case)-[:cites]->(c:Case {{name: '{citation_match}'}})\n"
    query += "RETURN o.name AS name"

    print(Panel(query, title="Cypher Query"))

    case_names = []
    with driver.session() as session:
        result = session.run(query)
        case_names.extend([record["name"] for record in result])

    # TODO check for empty result

    print("Cases with names:", str(case_names), "are matches")

    doc = retrieve_document(case_names[0])

    context = LegalQueryContext(
        doc=doc.page_content,
        query=query,
    )
    vector_db_client.close()

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
