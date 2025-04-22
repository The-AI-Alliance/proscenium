from typing import Callable

from pydantic import BaseModel
from rich import print
from uuid import uuid4, UUID
from neo4j import Driver


def query_to_prompts(
    query: str,
    query_extraction_model_id: str,
    milvus_uri: str,
    driver: Driver,
    query_extract: Callable[
        [str, str, bool], BaseModel
    ],  # (query_str, query_extraction_model_id) -> QueryExtractions
    query_extract_to_graph: Callable[
        [str, UUID, BaseModel, bool], None
    ],  # query, query_id, extract, verbose
    query_extract_to_context: Callable[
        [BaseModel, str, Driver, str, bool], BaseModel
    ],  # (QueryExtractions, query_str, Driver, milvus_uri) -> Context
    context_to_prompts: Callable[
        [BaseModel, bool], tuple[str, str]
    ],  # Context -> (system_prompt, user_prompt)
    verbose: bool = False,
) -> str:

    query_id = uuid4()

    print("Extracting information from the question")

    extract = query_extract(query, query_extraction_model_id, verbose)
    if extract is None:
        print("Unable to extract information from that question")
        return None

    if verbose:
        print("Extract:", extract)

    print("Storing the extracted information in the graph")
    query_extract_to_graph(query, query_id, extract, driver, verbose)

    print("Forming context from the extracted information")
    context = query_extract_to_context(extract, query, driver, milvus_uri, verbose)

    if verbose:
        print("Context:", context)

    prompts = context_to_prompts(context, verbose)

    return prompts
