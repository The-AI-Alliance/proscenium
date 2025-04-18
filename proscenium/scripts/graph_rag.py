from typing import Callable

from pydantic import BaseModel

from rich import print
from rich.panel import Panel

from neo4j import Driver

from proscenium.verbs.complete import complete_simple


def query_to_prompts(
    question: str,
    query_extraction_model_id: str,
    milvus_uri: str,
    driver: Driver,
    query_extract: Callable[
        [str, str, bool], BaseModel
    ],  # (query_str, query_extraction_model_id) -> QueryExtractions
    extract_to_context: Callable[
        [BaseModel, str, Driver, str, bool], BaseModel
    ],  # (QueryExtractions, query_str, Driver, milvus_uri) -> Context
    context_to_prompts: Callable[
        [BaseModel, bool], tuple[str, str]
    ],  # Context -> (system_prompt, user_prompt)
    verbose: bool = False,
) -> str:

    print("Extracting information from the question")
    extract = query_extract(question, query_extraction_model_id, verbose)
    if extract is None:
        print("Unable to extract information from that question")
        return None
    print("Extract:", extract)

    print("Forming context from the extracted information")
    context = extract_to_context(extract, question, driver, milvus_uri, verbose)
    print("Context:", context)

    prompts = context_to_prompts(context, verbose)

    return prompts
