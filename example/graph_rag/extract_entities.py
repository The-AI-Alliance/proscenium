
import logging
from rich import print
from rich.progress import Progress
import csv

from proscenium.read import load_hugging_face_dataset
from proscenium.parse import raw_extraction_template, PartialFormatter

from .config import num_docs, hf_dataset_id, hf_dataset_column
from .config import model_id, predicates, entity_csv_file, doc_display, doc_as_object, doc_direct_triples
from .extract_utils import process_document_chunks

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

docs = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)

old_len = len(docs)
docs = docs[:num_docs]
print("using the first", num_docs, "documents of", len(docs), "from HF dataset", hf_dataset_id)

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in predicates.items()]))

with Progress() as progress:

    task_extract = progress.add_task("[green]Extracting entities...", total=len(docs))

    with open(entity_csv_file, "wt") as f:

        writer = csv.writer(f, delimiter=",", quotechar='"')
        writer.writerow(["subject", "predicate", "object"]) # header

        for doc in docs:

            doc_display(doc)

            direct_triples = doc_direct_triples(doc)
            writer.writerows(direct_triples)

            object = doc_as_object(doc)
            process_document_chunks(model_id, extraction_template, predicates, doc, object, writer)

            progress.update(task_extract, advance=1)

    print("Wrote entity triples to", entity_csv_file)
