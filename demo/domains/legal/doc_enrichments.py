from typing import List, Optional, Callable
import logging
from pydantic import BaseModel, Field

from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from langchain_core.documents.base import Document

from eyecite import get_citations
from eyecite.models import CitationBase

from proscenium.verbs.extract import partial_formatter
from proscenium.verbs.extract import raw_extraction_template
from proscenium.scripts.document_enricher import extract_from_document_chunks
from proscenium.scripts.document_enricher import enrich_documents

from proscenium.core import Prop

from demo.domains.legal.docs import doc_as_rich
from demo.config import default_model_id

from demo.domains.legal.docs import retriever

log = logging.getLogger(__name__)


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


class DocumentEnrichments(Prop):

    def __init__(
        self,
        docs_per_dataset: int,
        output: Path,
        delay: float,
        console: Optional[Console] = None,
    ):
        super().__init__(console)
        self.docs_per_dataset = docs_per_dataset
        self.output = output
        self.delay = delay

    def build(self, force: bool = False):

        if self.output.exists() and not force:
            logging.info(
                f"Output file {self.output} already exists.",
            )
            return

        extract_from_opinion_chunks = make_extract_from_opinion_chunks(
            doc_as_rich,
            default_chunk_extraction_model_id,
            chunk_extraction_template,
            LegalOpinionChunkExtractions,
            delay=self.delay,
            console=self.console,
        )

        enrich_documents(
            retriever(self.docs_per_dataset),
            extract_from_opinion_chunks,
            doc_enrichments,
            self.output,
            console=self.console,
        )
