from typing import Callable
from typing import Any

import logging
import json
from pydantic import BaseModel
from rich.progress import Progress
from neo4j import Driver

log = logging.getLogger(__name__)


def load_knowledge_graph(
    driver: Driver,
    enrichments_jsonl_file: str,
    enrichments_clazz: type[BaseModel],
    doc_enrichments_to_graph: Callable[[Any, BaseModel], None],
) -> None:

    log.info("Parsing enrichments from %s", enrichments_jsonl_file)

    enrichmentss = []
    with open(enrichments_jsonl_file, "r") as f:
        for line in f:
            e = enrichments_clazz.model_construct(**json.loads(line))
            enrichmentss.append(e)

    with Progress() as progress:

        task_load = progress.add_task(
            f"Loading {len(enrichmentss)} enriched documents into graph...",
            total=len(enrichmentss),
        )

        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")  # empty graph
            for e in enrichmentss:
                session.execute_write(doc_enrichments_to_graph, e)
                progress.update(task_load, advance=1)
