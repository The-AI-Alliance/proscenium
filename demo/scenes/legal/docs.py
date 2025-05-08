from typing import List, Optional, Callable

import logging
from rich.panel import Panel
from langchain_core.documents.base import Document
from neo4j import Driver

from proscenium.verbs.read import load_hugging_face_dataset

log = logging.getLogger(__name__)

topic = "US Caselaw"

# hf_dataset_ids = ["free-law/nh", "free-law/Caselaw_Access_Project"]
hf_dataset_ids = ["free-law/nh"]
# Early version looked at only: free-law/nh ids {'4440632', '4441078'}

hf_dataset_column = "text"

default_docs_per_dataset = 10


def retrieve_documents(docs_per_dataset: int = None) -> List[Document]:

    docs = []

    for hf_dataset_id in hf_dataset_ids:

        dataset_docs = load_hugging_face_dataset(
            hf_dataset_id, page_content_column=hf_dataset_column
        )

        docs_in_dataset = len(dataset_docs)

        num_docs_to_use = docs_in_dataset
        if docs_per_dataset is not None:
            num_docs_to_use = min(docs_per_dataset, docs_in_dataset)

        log.info(
            f"using {num_docs_to_use}/{docs_in_dataset} documents from {hf_dataset_id}"
        ),

        for i in range(num_docs_to_use):
            doc = dataset_docs[i]
            doc.metadata["hf_dataset_id"] = hf_dataset_id
            doc.metadata["hf_dataset_index"] = i
            docs.append(doc)

    return docs


def retriever(docs_per_dataset: int) -> Callable[[], List[Document]]:

    def retrieve_documents_fn() -> List[Document]:
        return retrieve_documents(docs_per_dataset)

    return retrieve_documents_fn


def retrieve_document(id: str, driver: Driver) -> Optional[Document]:

    with driver.session() as session:
        result = session.run("MATCH (c: Case {name: $name}) RETURN c", name=id)

        head = result.single()["c"]
        if head is None:
            log.error("retrieve_document: no results for id %s", id)
            return None

        hf_dataset_id = head["hf_dataset_id"]
        index = int(head["hf_dataset_index"])

        docs = load_hugging_face_dataset(
            hf_dataset_id, page_content_column=hf_dataset_column
        )

        if 0 <= index < len(docs):
            return docs[index]
        else:
            return None


case_template = """
[u]{name}[/u]
{reporter}, Volume {volume} pages {first_page}-{last_page}
Court: {court}
Decision Date: {decision_date}
Citations: {citations}

Docket Number: {docket_number}
Jurisdiction: {jurisdiction}
Judges: {judges}
Parties: {parties}

Word Count: {word_count}, Character Count: {char_count}
Last Updated: {last_updated}, Provenance: {provenance}
Id: {id}
"""  # leaves out head_matter


def doc_as_rich(doc: Document):

    case_str = case_template.format_map(doc.metadata)

    return Panel(case_str, title=doc.metadata["name_abbreviation"])
