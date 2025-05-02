import logging
from pydantic import BaseModel, Field

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
