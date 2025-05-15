from typing import Callable
from typing import Optional

import logging

from rich.console import Console

from pydantic import BaseModel
from uuid import uuid4, UUID
from neo4j import Driver

log = logging.getLogger(__name__)


def query_to_prompts(
    query: str,
    query_extraction_model_id: str,
    milvus_uri: str,
    driver: Driver,
    query_extract: Callable[
        [str, str], BaseModel
    ],  # (query_str, query_extraction_model_id) -> QueryExtractions
    query_extract_to_graph: Callable[
        [str, UUID, BaseModel], None
    ],  # query, query_id, extract
    query_extract_to_context: Callable[
        [BaseModel, str, Driver, str, Optional[Console]], BaseModel
    ],  # (QueryExtractions, query_str, Driver, milvus_uri) -> Context
    context_to_prompts: Callable[
        [BaseModel], tuple[str, str]
    ],  # Context -> (system_prompt, user_prompt)
    console: Optional[Console] = None,
) -> Optional[tuple[str, str]]:

    query_id = uuid4()

    log.info("Extracting information from the question")

    extract = query_extract(query, query_extraction_model_id)
    if extract is None:
        log.info("Unable to extract information from that question")
        return None

    log.info("Extract: %s", extract)

    log.info("Storing the extracted information in the graph")
    query_extract_to_graph(query, query_id, extract, driver)

    log.info("Forming context from the extracted information")
    context = query_extract_to_context(
        extract, query, driver, milvus_uri, console=console
    )
    if context is None:
        log.info("Unable to form context from the extracted information")
        return None

    log.info("Context: %s", context)

    prompts = context_to_prompts(context)

    return prompts
