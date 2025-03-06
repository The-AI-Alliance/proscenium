
import logging
import csv
from rich import print
from rich.progress import Progress

from proscenium.read import load_hugging_face_dataset

# Problem-specific configuration:
import example.graph_rag.config as config
from example.graph_rag.util import process_document

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
