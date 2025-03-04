
from typing import List

import logging
import csv
from rich import print
from rich.progress import Progress
from langchain_core.documents.base import Document

from proscenium.read import load_hugging_face_dataset
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.parse import PartialFormatter
from proscenium.parse import raw_extraction_template
from proscenium.parse import get_triples_from_extract
from proscenium.complete import complete_simple

# Problem-specific configuration:
import example.graph_rag.config as config

##############################################
# Utilities for document and chunk processing
##############################################

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in config.predicates.items()]))


def process_chunk(chunk: Document, object: str) -> List[tuple[str, str, str]]:

    extract = complete_simple(
        config.model_id,
        "You are an entity extractor",
        extraction_template.format(text = chunk.page_content))

    new_triples = get_triples_from_extract(extract, object, config.predicates)

    return new_triples


def process_document(doc: Document) -> List[tuple[str, str, str]]:

    config.doc_display(doc)

    doc_triples = []

    direct_triples = config.doc_direct_triples(doc)
    doc_triples.extend(direct_triples)

    object = config.doc_as_object(doc)

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

docs = load_hugging_face_dataset(config.hf_dataset_id, page_content_column=config.hf_dataset_column)

old_len = len(docs)
docs = docs[:config.num_docs]
print("using the first", config.num_docs, "documents of", len(docs), "from HF dataset", config.hf_dataset_id)

with Progress() as progress:

    task_extract = progress.add_task("[green]Extracting entities...", total=len(docs))

    with open(config.entity_csv_file, "wt") as f:

        writer = csv.writer(f, delimiter=",", quotechar='"')
        writer.writerow(["subject", "predicate", "object"]) # header

        for doc in docs:

            doc_triples = process_document(doc)
            writer.writerows(doc_triples)
            progress.update(task_extract, advance=1)

    print("Wrote entity triples to", config.entity_csv_file)
