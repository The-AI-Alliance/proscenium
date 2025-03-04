
from typing import List
import logging
from rich import print
from rich.progress import Progress
import csv
from langchain_core.documents.base import Document
from proscenium.parse import PartialFormatter

from proscenium.read import load_hugging_face_dataset
from proscenium.parse import raw_extraction_template
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.parse import get_triples_from_extract
from proscenium.complete import complete_simple

##############################################
# Problem-specific configuration imports
##############################################

from .config import num_docs, hf_dataset_id, hf_dataset_column
from .config import model_id
from .config import predicates
from .config import doc_display, doc_as_object, doc_direct_triples
from .config import entity_csv_file

##############################################
# Utilities for document and chunk processing
##############################################

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in predicates.items()]))


def process_chunk(chunk: Document, object: str) -> List[tuple[str, str, str]]:

    extract = complete_simple(
        model_id,
        "You are an entity extractor",
        extraction_template.format(text = chunk.page_content))

    new_triples = get_triples_from_extract(extract, object, predicates)

    return new_triples


def process_document(doc: Document) -> List[tuple[str, str, str]]:

    doc_display(doc)

    doc_triples = []

    direct_triples = doc_direct_triples(doc)
    doc_triples.extend(direct_triples)

    object = doc_as_object(doc)

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        new_triples = process_chunk(chunk, object)
        print("Found", len(new_triples), "triples in chunk", i+1, "of", len(chunks))

        doc_triples.extend(new_triples)

    return doc_triples

##############################################
# Main
##############################################

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

docs = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)

old_len = len(docs)
docs = docs[:num_docs]
print("using the first", num_docs, "documents of", len(docs), "from HF dataset", hf_dataset_id)

with Progress() as progress:

    task_extract = progress.add_task("[green]Extracting entities...", total=len(docs))

    with open(entity_csv_file, "wt") as f:

        writer = csv.writer(f, delimiter=",", quotechar='"')
        writer.writerow(["subject", "predicate", "object"]) # header

        for doc in docs:

            doc_triples = process_document(doc)
            writer.writerows(doc_triples)
            progress.update(task_extract, advance=1)

    print("Wrote entity triples to", entity_csv_file)
