from typing import Optional, Generator

import logging
import json
from rich.console import Console
from rich.panel import Panel
from uuid import UUID
from pydantic import BaseModel, Field
from neo4j import Driver
from eyecite import get_citations

from proscenium.core import Character
from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import extraction_system_prompt
from proscenium.verbs.extract import raw_extraction_template
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.vector_database import vector_db
from proscenium.patterns.graph_rag import query_to_prompts

from demo.config import default_model_id
from demo.scenes.legal.docs import retrieve_document
from demo.scenes.legal.docs import topic

log = logging.getLogger(__name__)

user_prompt = f"What is your question about {topic}?"

# default_question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"
default_question = "How has 291 A.2d 605 been used in NH caselaw?"


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
    query: str, query_extraction_model_id: str, console: Optional[Console] = None
) -> QueryExtractions:

    user_prompt = query_extraction_template.format(text=query)

    if console is not None:
        console.print(Panel(user_prompt, title="Query Extraction Prompt"))

    extract = complete_simple(
        query_extraction_model_id,
        extraction_system_prompt,
        user_prompt,
        response_format={
            "type": "json_object",
            "schema": QueryExtractions.model_json_schema(),
        },
        console=console,
    )

    if console is not None:
        console.print(Panel(str(extract), title="Query Extraction String"))

    try:

        qe_json = json.loads(extract)
        result = QueryExtractions(**qe_json)
        return result

    except Exception as e:

        log.error("query_extract: Exception: %s", e)

    return None


def query_extract_to_graph(
    query: str,
    query_id: UUID,
    qe: QueryExtractions,
    driver: Driver,
) -> None:

    with driver.session() as session:
        # TODO manage the query logging in a separate namespace from the
        # domain graph
        query_save_result = session.run(
            "CREATE (:Query {id: $query_id, value: $value})",
            query_id=str(query_id),
            value=query,
        )
        log.info(f"Saved query {query} with id {query_id} to the graph")
        log.info(query_save_result.consume())

        for judgeref in qe.judge_names:
            session.run(
                "MATCH (q:Query {id: $query_id}) "
                + "MERGE (q)-[:mentions]->(:JudgeRef {text: $judgeref, confidence: $confidence})",
                query_id=str(query_id),
                judgeref=judgeref,
                confidence=0.6,
            )


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
    console: Optional[Console] = None,
) -> LegalQueryContext:

    vector_db_client = vector_db(milvus_uri)

    try:
        caserefs = get_citations(query)

        case_judgeref_clauses = []
        if qe is not None:
            case_judgeref_clauses = [
                # TODO judgeref_match = find_matching_objects(vector_db_client, judgeref, judge_resolver)
                f"MATCH (c:Case)-[:mentions]->(:JudgeRef {{text: '{judgeref}'}})"
                for judgeref in qe.judge_names
            ]

        case_caseref_clauses = [
            # TODO caseref_match = find_matching_objects(vector_db_client, caseref, case_resolver)
            f"MATCH (c:Case)-[:mentions]->(:CaseRef {{text: '{caseref.matched_text()}'}})"
            for caseref in caserefs
        ]

        case_match_clauses = case_judgeref_clauses + case_caseref_clauses

        if len(case_match_clauses) == 0:
            log.warning("No case match clauses found")
            return None

        cypher = "\n".join(case_match_clauses) + "\nRETURN c.name AS name"

        if console is not None:
            console.print(Panel(cypher, title="Cypher Query"))

        case_names = []
        with driver.session() as session:
            result = session.run(cypher)
            case_names.extend([record["name"] for record in result])

        # TODO check for empty result
        log.info("Cases with names: %s mention %s", str(case_names), str(caserefs))

        # TODO: take all docs -- not just head
        doc = retrieve_document(case_names[0], driver)

        context = LegalQueryContext(
            doc=doc.page_content,
            query=query,
        )
    finally:
        vector_db_client.close()

    return context


generation_system_prompt = "You are a helpful law librarian"

graphrag_prompt_template = """
Answer the question using the following text from one case:

{document_text}

Question: {question}
"""


def context_to_prompts(
    context: LegalQueryContext,
) -> tuple[str, str]:

    user_prompt = graphrag_prompt_template.format(
        document_text=context.doc, question=context.query
    )

    return generation_system_prompt, user_prompt


default_generation_model_id = default_model_id


class LawLibrarian(Character):
    """
    A law librarian that can answer questions about case law."""

    def __init__(self, driver: Driver, milvus_uri: str, admin_channel_id: str):
        super().__init__(admin_channel_id=admin_channel_id)
        self.driver = driver
        self.milvus_uri = milvus_uri

    def handle(
        self, channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:

        prompts = query_to_prompts(
            utterance,
            default_query_extraction_model_id,
            self.milvus_uri,
            self.driver,
            query_extract,
            query_extract_to_graph,
            query_extract_to_context,
            context_to_prompts,
        )

        if prompts is None:

            yield channel_id, "Sorry, I'm not able to answer that question."

        else:

            yield channel_id, "I think I can help with that..."

            system_prompt, user_prompt = prompts

            response = complete_simple(
                default_generation_model_id, system_prompt, user_prompt
            )

            yield channel_id, response
