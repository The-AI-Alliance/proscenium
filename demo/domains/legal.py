from typing import List, Optional, Callable
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

from proscenium.scripts.entity_resolver import Resolver
from proscenium.scripts.entity_resolver import find_matching_objects

from demo.config import default_model_id

from eyecite import get_citations
from eyecite.models import CitationBase

###################################
# Knowledge Graph Schema
###################################


class NodeLabel(StrEnum):
    Case = "Case"
    CaseRef = "CaseRef"
    JudgeRef = "JudgeRef"
    Judge = "Judge"
    GeoRef = "GeoRef"
    CompanyRef = "CompanyRef"


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

    # (mentioner) -> [:mentions] -> (ref)
    # (ref) -> [:references] -> (referent)

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
# retriever
###################################

topic = "US Caselaw"

# hf_dataset_ids = ["free-law/nh", "free-law/Caselaw_Access_Project"]
hf_dataset_ids = ["free-law/nh"]
# Early version looked at only: free-law/nh ids {'4440632', '4441078'}

hf_dataset_column = "text"


def retrieve_documents(docs_per_dataset: int = None) -> List[Document]:

    docs = []

    for hf_dataset_id in hf_dataset_ids:

        dataset_docs = load_hugging_face_dataset(
            hf_dataset_id, page_content_column=hf_dataset_column
        )

        docs_in_dataset = len(dataset_docs)

        num_docs_to_use = docs_in_dataset
        if docs_per_dataset is not None:
            num_docs_to_use = min(docs_per_dataset, docs_in_dataset)

        logging.info(
            f"using {num_docs_to_use}/{docs_in_dataset} documents from {hf_dataset_id}"
        ),

        for i in range(num_docs_to_use):
            doc = dataset_docs[i]
            doc.metadata["hf_dataset_id"] = hf_dataset_id
            doc.metadata["hf_dataset_index"] = i
            docs.append(doc)

    return docs


def retriever(docs_per_dataset: int) -> Callable[[], List[Document]]:

    def retrieve_documents_fn() -> List[Document]:
        return retrieve_documents(docs_per_dataset)

    return retrieve_documents_fn


def retrieve_document(id: str, driver: Driver) -> Optional[Document]:

    with driver.session() as session:
        result = session.run("MATCH (n) RETURN n.hf_dataset_index AS hf_dataset_index")
        if len(result) == 0:
            logging.warning("No node n found in the graph")
            return None

        head = result[0]
        hf_dataset_id = head["hf_dataset_id"]
        index = int(head["hf_dataset_index"])

        docs = load_hugging_face_dataset(
            hf_dataset_id, page_content_column=hf_dataset_column
        )

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
    The judge names, geographic locations, and company names mentioned in a chunk of a legal opinion.
    """

    judge_names: list[str] = Field(
        description="A list of the judge names in the text. For example: ['Judge John Doe', 'Judge Jane Smith']"
    )

    geographic_locations: list[str] = Field(
        description="A list of the geographic locations in the text. For example: ['New Hampshire', 'Portland, Maine', 'Elm Street']"
    )

    company_names: list[str] = Field(
        description="A list of the company names in the text. For example: ['Acme Corp', 'IBM', 'Bob's Auto Repair']"
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
    georefs: list[str] = Field(
        description="A list of the geographic locations mentioned in the text. For example: ['New Hampshire', 'Portland, Maine', 'Elm Street']"
    )
    companyrefs: list[str] = Field(
        description="A list of the company names mentioned in the text. For example: ['Acme Corp', 'IBM', 'Bob's Auto Repair']"
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
    georefs = []
    companyrefs = []
    for chunk_extract in chunk_extracts:
        if chunk_extract.__dict__.get("judge_names") is not None:
            judgerefs.extend(chunk_extract.judge_names)
        if chunk_extract.__dict__.get("geographic_locations") is not None:
            georefs.extend(chunk_extract.geographic_locations)
        if chunk_extract.__dict__.get("company_names") is not None:
            companyrefs.extend(chunk_extract.company_names)

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
        georefs=georefs,
        companyrefs=companyrefs,
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

    for georef in enrichments.georefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:GeoRef {text: $georef})",
            case=case_name,
            georef=georef,
        )

    for companyref in enrichments.companyrefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:CompanyRef {text: $companyref})",
            case=case_name,
            companyref=companyref,
        )


def show_knowledge_graph(driver: Driver):

    with driver.session() as session:

        node_types_result = session.run("MATCH (n) RETURN labels(n) AS nls")
        node_types = set()
        for record in node_types_result:
            node_types.update(record["nls"])
        ntt = Table(title="Node Types", show_lines=False)
        ntt.add_column("Type", justify="left")
        for nt in node_types:
            ntt.add_row(nt)
        print(ntt)

        relations_types_result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel")
        relation_types = [record["rel"] for record in relations_types_result]
        unique_relations = list(set(relation_types))
        rtt = Table(title="Relationship Types", show_lines=False)
        rtt.add_column("Type", justify="left")
        for rt in unique_relations:
            rtt.add_row(rt)
        print(rtt)

        cases_result = session.run("MATCH (n:Case) RETURN properties(n) AS p")
        cases_table = Table(title="Cases", show_lines=False)
        cases_table.add_column("Properties", justify="left")
        for case_record in cases_result:
            cases_table.add_row(str(case_record["p"]))
        print(cases_table)

        judgerefs_result = session.run("MATCH (n:JudgeRef) RETURN n.text AS text")
        judgerefs_table = Table(title="JudgeRefs", show_lines=False)
        judgerefs_table.add_column("Text", justify="left")
        for judgeref_record in judgerefs_result:
            judgerefs_table.add_row(judgeref_record["text"])
        print(judgerefs_table)

        caserefs_result = session.run("MATCH (n:CaseRef) RETURN n.text AS text")
        caserefs_table = Table(title="CaseRefs", show_lines=False)
        caserefs_table.add_column("Text", justify="left")
        for caseref_record in caserefs_result:
            caserefs_table.add_row(caseref_record["text"])
        print(caserefs_table)

        georefs_result = session.run("MATCH (n:GeoRef) RETURN n.text AS text")
        georefs_table = Table(title="GeoRefs", show_lines=False)
        georefs_table.add_column("Text", justify="left")
        for georef_record in georefs_result:
            georefs_table.add_row(georef_record["text"])
        print(georefs_table)

        companyrefs_result = session.run("MATCH (n:CompanyRef) RETURN n.text AS text")
        companyrefs_table = Table(title="CompanyRefs", show_lines=False)
        companyrefs_table.add_column("Text", justify="left")
        for companyref_record in companyrefs_result:
            companyrefs_table.add_row(companyref_record["text"])
        print(companyrefs_table)


###################################
# user_question
###################################

user_prompt = f"What is your question about {topic}?"

default_question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"

###################################
# query_extract
###################################

default_query_extraction_model_id = default_model_id


class QueryExtractions(BaseModel):
    """
    The judge names mentioned in the user query.
    """

    judge_names: list[str] = Field(
        description="A list of the judge names in the user query. For example: ['Judge John Doe', 'Judge Jane Smith']",
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

case_resolver = Resolver(
    "MATCH (cr:CaseRef) RETURN cr.text AS text",
    "text",
    "resolve_caserefs",
    embedding_model_id,
)

judge_resolver = Resolver(
    "MATCH (jr:JudgeRef) RETURN jr.text AS text",
    "text",
    "resolve_judgerefs",
    embedding_model_id,
)

resolvers = [case_resolver, judge_resolver]


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
        caseref_match = find_matching_objects(vector_db_client, caseref, case_resolver)
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
