from typing import List
from typing import Callable
from typing import Optional

import time
import logging
from pydantic import BaseModel

from rich.panel import Panel
from rich.console import Console
from rich.progress import Progress

from langchain_core.documents.base import Document

from proscenium.verbs.chunk import documents_to_chunks_by_tokens
from proscenium.verbs.extract import extract_to_pydantic_model


def extract_from_document_chunks(
    doc: Document,
    doc_as_rich: Callable[[Document], Panel],
    chunk_extraction_model_id: str,
    chunk_extraction_template: str,
    chunk_extract_clazz: type[BaseModel],
    delay: float,
    console: Optional[Console] = None,
) -> List[BaseModel]:

    if console is not None:
        console.print(doc_as_rich(doc))
        console.print()

    extract_models = []

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        ce = extract_to_pydantic_model(
            chunk_extraction_model_id,
            chunk_extraction_template,
            chunk_extract_clazz,
            chunk.page_content,
        )

        logging.info("Extract model in chunk %s of %s", i + 1, len(chunks))
        if console is not None:
            console.print(Panel(str(ce)))

        extract_models.append(ce)
        time.sleep(delay)

    return extract_models


def enrich_documents(
    retrieve_documents: Callable[[], List[Document]],
    extract_from_doc_chunks: Callable[[Document], List[BaseModel]],
    doc_enrichments: Callable[[Document, list[BaseModel]], BaseModel],
    enrichments_jsonl_file: str,
    console: Optional[Console] = None,
) -> None:

    docs = retrieve_documents()

    with Progress() as progress:

        task_enrich = progress.add_task(
            "[green]Enriching documents...", total=len(docs)
        )

        with open(enrichments_jsonl_file, "wt") as f:

            for doc in docs:

                chunk_extract_models = extract_from_doc_chunks(doc)
                enrichments = doc_enrichments(doc, chunk_extract_models)
                enrichments_json = enrichments.model_dump_json()
                f.write(enrichments_json + "\n")

                progress.update(task_enrich, advance=1)

        logging.info("Wrote document enrichments to %s", enrichments_jsonl_file)
