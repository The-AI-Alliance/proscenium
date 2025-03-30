from typing import Callable

from pydantic import BaseModel

from rich import print
from rich.panel import Panel

from neo4j import Driver

from pymilvus import MilvusClient

from proscenium.verbs.complete import complete_simple


def answer_question(
    question: str,
    query_extraction_model_id: str,
    vector_db_client: MilvusClient,
    embedding_model_id: str,
    driver: Driver,
    generation_model_id: str,
    query_extract: Callable[
        [str, str], BaseModel
    ],  # (query_str, query_extraction_model_id) -> QueryExtractions
    extract_to_context: Callable[
        [BaseModel, str, Driver, MilvusClient], BaseModel
    ],  # (QueryExtractions, query_str, Driver, MilvusClient) -> Context
    context_to_prompts: Callable[
        [BaseModel], tuple[str, str]
    ],  # Context -> (system_prompt, user_prompt)
) -> str:

    print(Panel(question, title="Question"))

    print("Extracting information from the question")
    extract = query_extract(question, query_extraction_model_id)
    if extract is None:
        print("Unable to extract information from that question")
        return None
    print("Extract:", extract)

    print("Forming context from the extracted information")
    context = extract_to_context(
        extract, question, driver, vector_db_client, embedding_model_id
    )
    print("Context:", context)

    prompts = context_to_prompts(context, generation_model_id)

    if prompts is None:

        return None

    else:

        system_prompt, user_prompt = prompts

        response = complete_simple(
            generation_model_id, system_prompt, user_prompt, rich_output=True
        )

        return response
