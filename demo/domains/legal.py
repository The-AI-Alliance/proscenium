from typing import List, Optional, Callable, Generator
from enum import StrEnum

import logging
import json
from rich import print
from rich.panel import Panel
from rich.table import Table
from uuid import UUID
from neo4j import GraphDatabase

from langchain_core.documents.base import Document

from pydantic import BaseModel, Field

from neo4j import Driver
from neo4j.data import Record

from proscenium.verbs.read import load_hugging_face_dataset
from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import extraction_system_prompt
from proscenium.verbs.extract import raw_extraction_template
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.document_enricher import extract_from_document_chunks
from proscenium.scripts.document_enricher import enrich_documents
from proscenium.scripts.knowledge_graph import load_knowledge_graph
from proscenium.scripts.entity_resolver import Resolver
from proscenium.scripts.entity_resolver import load_entity_resolver
from proscenium.scripts.entity_resolver import find_matching_objects
from proscenium.scripts.graph_rag import query_to_prompts

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

default_docs_per_dataset = 10


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
        result = session.run("MATCH (c: Case {name: $name}) RETURN c", name=id)

        head = result.single()["c"]
        if head is None:
            logging.error("retrieve_document: no results for id %s", id)
            return None

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

default_delay = 1.0  # intra-chunk delay between inference calls


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
    cited_as: str = Field(description="how the opinion is cited")
    court: str = Field(description="name of the court")
    decision_date: str = Field(description="date of the decision")
    docket_number: str = Field(description="docket number of the case")
    jurisdiction: str = Field(description="jurisdiction of the case")
    judges: str = Field(description="authoring judges")
    parties: str = Field(description="parties in the case")
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

    print(doc.metadata)

    enrichments = LegalOpinionEnrichments(
        name=doc.metadata["name_abbreviation"],
        reporter=doc.metadata["reporter"],
        volume=doc.metadata["volume"],
        first_page=str(doc.metadata["first_page"]),
        last_page=str(doc.metadata["last_page"]),
        cited_as=doc.metadata["citations"],
        court=doc.metadata["court"],
        decision_date=doc.metadata["decision_date"],
        docket_number=doc.metadata["docket_number"],
        jurisdiction=doc.metadata["jurisdiction"],
        judges=doc.metadata["judges"],
        parties=doc.metadata["parties"],
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


def extract_from_opinion_chunks_function(
    doc_as_rich: Callable[[Document], Panel],
    chunk_extraction_model_id: str,
    chunk_extraction_template: str,
    chunk_extract_clazz: type[BaseModel],
    delay: float = 1.0,  # intra-chunk delay between inference calls
) -> Callable[[Document, bool], List[BaseModel]]:

    def extract_from_doc_chunks(
        doc: Document, verbose: bool = False
    ) -> List[BaseModel]:

        chunk_extract_models = extract_from_document_chunks(
            doc,
            doc_as_rich,
            chunk_extraction_model_id,
            chunk_extraction_template,
            chunk_extract_clazz,
            delay,
            verbose,
        )

        return chunk_extract_models

    return extract_from_doc_chunks


###################################
# make_document_enricher
###################################

from pathlib import Path


def make_document_enricher(
    docs_per_dataset: int, output: Path, delay: float, verbose: bool = False
) -> Callable[[bool], None]:

    def enrich(force: bool = False):

        if output.exists() and not force:
            print(
                f"Output file {output} already exists.",
            )
            return

        extract_from_opinion_chunks = extract_from_opinion_chunks_function(
            doc_as_rich,
            default_chunk_extraction_model_id,
            chunk_extraction_template,
            LegalOpinionChunkExtractions,
            delay=delay,
        )

        enrich_documents(
            retriever(docs_per_dataset),
            extract_from_opinion_chunks,
            doc_enrichments,
            output,
            verbose=verbose,
        )

    return enrich


###################################
# make_kg_loader
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
        + "cited_as: $cited_as, "
        + "court: $court, decision_date: $decision_date, "
        + "docket_number: $docket_number, jurisdiction: $jurisdiction, "
        + "hf_dataset_id: $hf_dataset_id, hf_dataset_index: $hf_dataset_index"
        + "})",
        case=case_name,
        reporter=enrichments.reporter,
        volume=enrichments.volume,
        first_page=enrichments.first_page,
        last_page=enrichments.last_page,
        cited_as=enrichments.cited_as,
        court=enrichments.court,
        decision_date=enrichments.decision_date,
        docket_number=enrichments.docket_number,
        jurisdiction=enrichments.jurisdiction,
        hf_dataset_id=enrichments.hf_dataset_id,
        hf_dataset_index=enrichments.hf_dataset_index,
    )

    # Resolvable fields from the document metadata

    # TODO split multiple judges upstream
    judge = enrichments.judges
    if len(judge) > 0:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:authored_by]->(:JudgeRef {text: $judge, confidence: $confidence})",
            judge=judge,
            case=case_name,
            confidence=0.9,
        )
    # TODO split into plaintiff(s) and defendant(s) upstream
    parties = enrichments.parties
    tx.run(
        "MATCH (c:Case {name: $case}) "
        + "MERGE (c)-[:involves]->(:PartyRef {name: $party, confidence: $confidence})",
        party=parties,
        case=case_name,
        confidence=0.9,
    )

    # Fields extracted from the text with LLM:

    for judgeref in enrichments.judgerefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:JudgeRef {text: $judgeref, confidence: $confidence})",
            judgeref=judgeref,
            case=case_name,
            confidence=0.6,
        )

    for caseref in enrichments.caserefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:CaseRef {text: $caseref, confidence: $confidence})",
            case=case_name,
            caseref=caseref,
            confidence=0.6,
        )

    for georef in enrichments.georefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:GeoRef {text: $georef, confidence: $confidence})",
            case=case_name,
            georef=georef,
            confidence=0.6,
        )

    for companyref in enrichments.companyrefs:
        tx.run(
            "MATCH (c:Case {name: $case}) "
            + "MERGE (c)-[:mentions]->(:CompanyRef {text: $companyref, confidence: $confidence})",
            case=case_name,
            companyref=companyref,
            confidence=0.6,
        )


def make_kg_loader(
    input: Path,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    verbose: bool = False,
) -> Callable[[bool], None]:

    def load(force: bool = False):

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

        num_nodes = 0
        with driver.session() as session:
            num_nodes = session.run("MATCH (n) RETURN COUNT(n) AS cnt").single().value()

        if num_nodes > 0 and not force:
            print(
                f"Knowledge graph already exists at {neo4j_uri} and has at least one node.",
                "Skipping its load.",
            )
            driver.close()
            return

        load_knowledge_graph(
            driver,
            input,
            LegalOpinionEnrichments,
            doc_enrichments_to_graph,
        )

        driver.close()

    return load


###################################
# make_kg_shower
###################################


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


def make_kg_shower(
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
) -> Callable[[bool], None]:

    def show(force: bool = False):
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))
        show_knowledge_graph(driver)
        driver.close()

    return show


###################################
# make_entity_resolver_loader
###################################


def make_entity_resolver_loader(
    milvus_uri: str,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    verbose: bool = False,
) -> Callable[[bool], None]:

    def load(force: bool = False):

        # TODO check if the resolvers are already loaded

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

        load_entity_resolver(
            driver,
            resolvers,
            milvus_uri,
        )

        driver.close()

    return load


###################################
# prerequisites
###################################


def prerequisites(
    docs_per_dataset: int,
    enrichment_jsonl_file: Path,
    delay: float,
    neo4j_uri: str,
    neo4j_username: str,
    neo4j_password: str,
    milvus_uri: str,
    verbose: bool = False,
) -> List[Callable[[bool], None]]:

    enrich = make_document_enricher(
        docs_per_dataset, enrichment_jsonl_file, delay, verbose
    )

    load_kg = make_kg_loader(
        enrichment_jsonl_file, neo4j_uri, neo4j_username, neo4j_password, verbose
    )

    load_resolver = make_entity_resolver_loader(
        milvus_uri,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        verbose,
    )

    return [
        enrich,
        load_kg,
        load_resolver,
    ]


###################################
# user_question
###################################

user_prompt = f"What is your question about {topic}?"

# default_question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"
default_question = "How has 291 A.2d 605 been used in NH caselaw?"

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


def query_extract(
    query: str, query_extraction_model_id: str, verbose: bool = False
) -> QueryExtractions:

    user_prompt = query_extraction_template.format(text=query)

    if verbose:
        print(Panel(user_prompt, title="Query Extraction Prompt"))

    extract = complete_simple(
        query_extraction_model_id,
        extraction_system_prompt,
        user_prompt,
        response_format={
            "type": "json_object",
            "schema": QueryExtractions.model_json_schema(),
        },
        rich_output=verbose,
    )

    if verbose:
        print(Panel(str(extract), title="Query Extraction String"))

    try:

        qe_json = json.loads(extract)
        result = QueryExtractions(**qe_json)
        return result

    except Exception as e:

        logging.error("query_extract: Exception: %s", e)

    return None


def query_extract_to_graph(
    query: str,
    query_id: UUID,
    qe: QueryExtractions,
    driver: Driver,
    verbose: bool = False,
) -> None:

    with driver.session() as session:
        # TODO manage the query logging in a separate namespace from the
        # domain graph
        query_save_result = session.run(
            "CREATE (:Query {id: $query_id, value: $value})",
            query_id=str(query_id),
            value=query,
        )
        if verbose:
            print(f"Saved query {query} with id {query_id} to the graph")
            print(query_save_result.consume())

        for judgeref in qe.judge_names:
            session.run(
                "MATCH (q:Query {id: $query_id}) "
                + "MERGE (q)-[:mentions]->(:JudgeRef {text: $judgeref, confidence: $confidence})",
                query_id=str(query_id),
                judgeref=judgeref,
                confidence=0.6,
            )


###################################
# query_extract_to_context
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


def query_extract_to_context(
    qe: QueryExtractions,
    query: str,
    driver: Driver,
    milvus_uri: str,
    verbose: bool = False,
) -> LegalQueryContext:

    vector_db_client = vector_db(milvus_uri)

    cypher = ""
    if qe is not None:
        for judgeref in qe.judge_names:
            # TODO judgeref_match = find_matching_objects(vector_db_client, judgeref, judge_resolver)
            cypher += (
                f"MATCH (c:Case)-[:mentions]->(:JudgeRef {{text: '{judgeref}'}})\n"
            )

    cypher = ""
    caserefs = get_citations(query)
    for caseref in caserefs:
        # TODO caseref_match = find_matching_objects(vector_db_client, caseref, case_resolver)
        cypher += f"MATCH (c:Case)-[:mentions]->(:CaseRef {{text: '{caseref.matched_text()}'}})\n"
    cypher += "RETURN c.name AS name"

    if verbose:
        print(Panel(cypher, title="Cypher Query"))

    case_names = []
    with driver.session() as session:
        result = session.run(cypher)
        case_names.extend([record["name"] for record in result])

    # TODO check for empty result
    print("Cases with names:", str(case_names), "mention", str(caserefs))

    # TODO: take all docs -- not just head
    doc = retrieve_document(case_names[0], driver)

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


def context_to_prompts(
    context: LegalQueryContext, verbose: bool = False
) -> tuple[str, str]:

    user_prompt = graphrag_prompt_template.format(
        document_text=context.doc, question=context.query
    )

    return generation_system_prompt, user_prompt


###################################
# generation
###################################

default_generation_model_id = default_model_id

###################################
# make_handler
###################################


def make_handler(
    driver: Driver, milvus_uri: str, verbose: bool = False
) -> Callable[[str], Generator[str, None, None]]:

    def handle(question: str) -> Generator[str, None, None]:

        prompts = query_to_prompts(
            question,
            default_query_extraction_model_id,
            milvus_uri,
            driver,
            query_extract,
            query_extract_to_graph,
            query_extract_to_context,
            context_to_prompts,
            verbose,
        )

        if prompts is None:

            yield "Sorry, I'm not able to answer that question."

        else:

            yield "I think I can help with that..."

            system_prompt, user_prompt = prompts

            response = complete_simple(
                default_generation_model_id,
                system_prompt,
                user_prompt,
                rich_output=verbose,
            )

            yield response

    return handle
