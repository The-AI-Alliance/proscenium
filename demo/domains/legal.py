from typing import List, Optional
from enum import StrEnum

import logging
import json
from rich import print
from rich.panel import Panel
from rich.table import Table

from langchain_core.documents.base import Document

from pydantic import BaseModel, Field

from neo4j import Driver

from proscenium.verbs.read import load_hugging_face_dataset
from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import extraction_system_prompt
from proscenium.verbs.extract import raw_extraction_template
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.entity_resolver import ReferenceResolver
from proscenium.scripts.entity_resolver import find_matching_objects

from demo.config import default_model_id

from eyecite import get_citations
from eyecite.models import CitationBase

###################################
# Knowledge Graph Schema
###################################


class NodeLabel(StrEnum):
    Judge = "Judge"
    JudgeRef = "JudgeRef"
    Case = "Case"
    CaseRef = "CaseRef"


class RelationLabel(StrEnum):
    mentions = "mentions"
    references = "references"


# TODO `ReferenceSchema` may move to `proscenium.scripts.knowledge_graph`
# depending on how much potentially resuable behavior is built around it


class ReferenceSchema:
    """
    A `ReferenceSchema` is a way of denoting the text span used to establish
    a relationship between two nodes in the knowledge graph.
    """

    # [mentioner] -> [:mentions] -> [ref]
    # [ref] -> [:references] -> [referent]

    # All fields refer to node labels
    def __init__(self, mentioners: list[str], ref_label: str, referent: str):
        self.mentioners = mentioners
        self.ref_label = ref_label
        self.referent = referent


judge_ref = ReferenceSchema(
    [NodeLabel.Case],
    NodeLabel.JudgeRef,
    NodeLabel.Judge,
)

case_ref = ReferenceSchema(
    [NodeLabel.Case],
    NodeLabel.CaseRef,
    NodeLabel.Case,
)

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
        doc.metadata["hf_dataset_id"] = hf_dataset_id
        doc.metadata["hf_dataset_index"] = i

    return docs


def retrieve_document(id: str, driver: Driver) -> Optional[Document]:

    docs = load_hugging_face_dataset(
        hf_dataset_id, page_content_column=hf_dataset_column
    )

    with driver.session() as session:
        result = session.run("MATCH (n) RETURN n.hf_dataset_index AS hf_dataset_index")
        if len(result) == 0:
            logging.warning("No node n found in the graph")
            return None

        index = int(result[0]["hf_dataset_index"])

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

default_chunk_extraction_model_id = default_model_id


class LegalOpinionChunkExtractions(BaseModel):
    """
    The judge names mentioned in a chunk of a legal opinion.
    """

    judge_names: list[str] = Field(
        description="A list of the judge names in the text. For example: ['Judge John Doe', 'Judge Jane Smith']",
    )


class LegalOpinionEnrichments(BaseModel):
    """
    Enrichments for a legal opinion document.
    """

    # Fields that come directly from the document metadata
    name: str = Field(description="opinion identifier; name abbreviation")
    reporter: str = Field(description="name of the publising reporter")
    volume: str = Field(description="volume number of the reporter")
    first_page: str = Field(description="first page number of the opinion")
    last_page: str = Field(description="last page number of the opinion")
    court: str = Field(description="name of the court")
    decision_date: str = Field(description="date of the decision")
    # TODO use (incoming) citations comes with the document
    docket_number: str = Field(description="docket number of the case")
    jurisdiction: str = Field(description="jurisdiction of the case")
    # TODO note that judges comes with the document, pre-extracted
    # TODO parties
    # TODO word_count, char_count, last_updated, provenance, id

    # Extracted from the text without LLM
    caserefs: list[str] = Field(
        description="A list of the legal citations in the text.  For example: ['123 F.3d 456', '456 F.3d 789']"
    )

    # Extracted from the text with LLM
    judgerefs: list[str] = Field(
        description="A list of the judge names mentioned in the text. For example: ['Judge John Doe', 'Judge Jane Smith']"
    )
    # Denoted by Proscenium framework
    hf_dataset_id: str = Field(description="id of the dataset in HF")
    hf_dataset_index: int = Field(description="index of the document in the HF dataset")


def doc_enrichments(
    doc: Document, chunk_extracts: list[LegalOpinionChunkExtractions]
) -> LegalOpinionEnrichments:

    citations: List[CitationBase] = get_citations(doc.page_content)

    # merge information from all chunks
    judgerefs = []
    for chunk_extract in chunk_extracts:
        if chunk_extract.__dict__.get("judge_names") is not None:
            judgerefs.extend(chunk_extract.judge_names)

    print(str(doc.metadata))

    enrichments = LegalOpinionEnrichments(
        name=doc.metadata["name_abbreviation"],
        reporter=doc.metadata["reporter"],
        volume=doc.metadata["volume"],
        first_page=str(doc.metadata["first_page"]),
        last_page=str(doc.metadata["last_page"]),
        court=doc.metadata["court"],
        decision_date=doc.metadata["decision_date"],
        docket_number=doc.metadata["docket_number"],
        jurisdiction=doc.metadata["jurisdiction"],
        caserefs=[c.matched_text() for c in citations],
        judgerefs=judgerefs,
        hf_dataset_id=doc.metadata["hf_dataset_id"],
        hf_dataset_index=int(doc.metadata["hf_dataset_index"]),
    )

    return enrichments


chunk_extraction_template = partial_formatter.format(
    raw_extraction_template, extraction_description=LegalOpinionChunkExtractions.__doc__
)


###################################
# Knowledge Graph
###################################


def doc_enrichments_to_graph(tx, enrichments: LegalOpinionEnrichments) -> None:
    """
    See https://neo4j.com/docs/cypher-manual/current/clauses/merge/ for
    Cypher semantics of MERGE.
    """

    case_name = enrichments.name

    tx.run(
        "MERGE (c:Case {"
        + "name: $case, "
        + "reporter: $reporter, volume: $volume, "
        + "first_page: $first_page, last_page: $last_page, "
        + "court: $court, decision_date: $decision_date, "
        + "docket_number: $docket_number, jurisdiction: $jurisdiction, "
        + "hf_dataset_id: $hf_dataset_id, hf_dataset_index: $hf_dataset_index"
        + "})",
        case=case_name,
        reporter=enrichments.reporter,
        volume=enrichments.volume,
        first_page=enrichments.first_page,
        last_page=enrichments.last_page,
        court=enrichments.court,
        decision_date=enrichments.decision_date,
        docket_number=enrichments.docket_number,
        jurisdiction=enrichments.jurisdiction,
        hf_dataset_id=enrichments.hf_dataset_id,
        hf_dataset_index=enrichments.hf_dataset_index,
    )

    for judgeref in enrichments.judgerefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:JudgeRef {text: $judgeref})",
            judgeref=judgeref,
            case=case_name,
        )

    for caseref in enrichments.caserefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:CaseRef {text: $caseref})",
            case=case_name,
            caseref=caseref,
        )


def show_knowledge_graph(driver: Driver):

    with driver.session() as session:

        cases_result = session.run("MATCH (n:Case) RETURN properties(n) AS p")
        cases_table = Table(title="Cases", show_lines=False)
        cases_table.add_column("Properties", justify="left")
        for case_record in cases_result:
            cases_table.add_row(str(case_record["p"]))
        print(cases_table)

        judgerefs_result = session.run("MATCH (n:JudgeRef) RETURN n.name AS name")
        judgerefs_table = Table(title="JudgeRefs", show_lines=False)
        judgerefs_table.add_column("Text", justify="left")
        for judgeref_record in judgerefs_result:
            judgerefs_table.add_row(judgeref_record["text"])
        print(judgerefs_table)

        caserefs_result = session.run("MATCH (n:CaseRef) RETURN n.name AS name")
        caserefs_table = Table(title="CaseRefs", show_lines=False)
        caserefs_table.add_column("Text", justify="left")
        for caseref_record in caserefs_result:
            caserefs_table.add_row(caseref_record["text"])
        print(caserefs_table)

        # all relations
        result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel")
        relations = [record["rel"] for record in result]
        unique_relations = list(set(relations))
        table = Table(title="Relationship Types", show_lines=False)
        table.add_column("Relationship Type", justify="left")
        for r in unique_relations:
            table.add_row(r)
        print(table)


###################################
# user_question
###################################

user_prompt = f"What is your question about {hf_dataset_id}?"

default_question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"

###################################
# query_extract
###################################

default_query_extraction_model_id = default_model_id


class QueryExtractions(BaseModel):
    """
    The extracted judges from the user query.
    """

    judgerefs: list[str] = Field(
        description="A list of the judges mentioned in the query. For example: `Judge John Doe`"
    )
    # caserefs: list[str] = Field(description = "A list of the legal citations in the query.  For example: `123 F.3d 456`")


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

citation_resolver = ReferenceResolver(
    "Case",
    "CaseRef",
    ["Case"],
    "MATCH (c:CaseRef) RETURN c.name AS name",
    "name",
    "resolve_caserefs",
    embedding_model_id,
)

judge_resolver = ReferenceResolver(
    "Judge",
    "JudgeRef",
    ["Case"],
    "MATCH (j:JudgeRefs) RETURN j.name AS name",
    "name",
    "resolve_judgerefs",
    embedding_model_id,
)

resolvers = [citation_resolver, judge_resolver]


class LegalQueryContext(BaseModel):
    """
    Context for generating answer in response to legal question.
    """

    doc: str = Field(
        description="The retrieved document text that is relevant to the question."
    )
    query: str = Field(description="The original question asked by the user.")
    # caserefs: list[str] = Field(description = "A list of the legal citations in the text.  For example: `123 F.3d 456`")


def extract_to_context(
    qe: QueryExtractions, query: str, driver: Driver, milvus_uri: str
) -> LegalQueryContext:

    vector_db_client = vector_db(milvus_uri)

    query = ""

    # TODO use judge (not judgref) from query

    caserefs = get_citations(query)
    for caseref in caserefs:
        caseref_match = find_matching_objects(
            vector_db_client, caseref, citation_resolver
        )
        query += (
            f"MATCH (c:Case)-[:mentions]->(r:CaseRef {{name: '{caseref_match}'}})\n"
        )
    query += "RETURN c.name AS name"

    print(Panel(query, title="Cypher Query"))

    case_names = []
    with driver.session() as session:
        result = session.run(query)
        case_names.extend([record["name"] for record in result])

    # TODO check for empty result

    print("Cases with names:", str(case_names), "mention", str(caserefs))

    # TODO: take all docs -- not just head
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
