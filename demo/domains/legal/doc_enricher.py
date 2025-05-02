from typing import List, Optional, Callable

import logging
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from langchain_core.documents.base import Document
from pydantic import BaseModel

from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import raw_extraction_template
from proscenium.scripts.document_enricher import extract_from_document_chunks
from proscenium.scripts.document_enricher import enrich_documents

from demo.domains.legal.docs import doc_as_rich
from demo.domains.legal.doc_enrichments import LegalOpinionChunkExtractions
from demo.domains.legal.doc_enrichments import LegalOpinionEnrichments
from demo.config import default_model_id

from eyecite import get_citations
from eyecite.models import CitationBase

from demo.domains.legal.docs import retriever

log = logging.getLogger(__name__)

# `judge` is not well captured in many of these documents,
# so we will extract it from the text

default_chunk_extraction_model_id = default_model_id

default_delay = 1.0  # intra-chunk delay between inference calls


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

    logging.info(doc.metadata)

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


def make_extract_from_opinion_chunks(
    doc_as_rich: Callable[[Document], Panel],
    chunk_extraction_model_id: str,
    chunk_extraction_template: str,
    chunk_extract_clazz: type[BaseModel],
    delay: float = 1.0,  # intra-chunk delay between inference calls
    console: Optional[Console] = None,
) -> Callable[[Document, bool], List[BaseModel]]:

    def extract_from_doc_chunks(doc: Document) -> List[BaseModel]:

        chunk_extract_models = extract_from_document_chunks(
            doc,
            doc_as_rich,
            chunk_extraction_model_id,
            chunk_extraction_template,
            chunk_extract_clazz,
            delay,
            console=console,
        )

        return chunk_extract_models

    return extract_from_doc_chunks


def make_document_enricher(
    docs_per_dataset: int, output: Path, delay: float, console: Optional[Console] = None
) -> Callable[[bool], None]:

    def enrich(force: bool = False):

        if output.exists() and not force:
            logging.info(
                f"Output file {output} already exists.",
            )
            return

        extract_from_opinion_chunks = make_extract_from_opinion_chunks(
            doc_as_rich,
            default_chunk_extraction_model_id,
            chunk_extraction_template,
            LegalOpinionChunkExtractions,
            delay=delay,
            console=console,
        )

        enrich_documents(
            retriever(docs_per_dataset),
            extract_from_opinion_chunks,
            doc_enrichments,
            output,
            console=console,
        )

    return enrich
