
import logging
import csv
from rich import print
from rich.progress import Progress

from langchain_core.documents.base import Document
from proscenium.read import load_hugging_face_dataset
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.parse import get_triples_from_extract
from proscenium.parse import extraction_template_from_categories
from proscenium.complete import complete_simple
from proscenium.write import triples_to_csv

from .config import categories
from .config import model_id
from .display import display_case
from .config import entity_csv_file
from .config import num_docs, hf_dataset_id, hf_dataset_column

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

def process_document(extraction_template: str, case_doc: Document, writer: csv.writer):

    case_name = case_doc.metadata['name_abbreviation']

    writer.writerow((case_doc.metadata["court"], 'Court', case_name))

    chunks = documents_to_chunks_by_tokens([case_doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        print("chunk", i+1, "of", len(chunks))

        extract = complete_simple(
            model_id,
            "You are an entity extractor",
            extraction_template.format(text = chunk.page_content))

        new_triples = get_triples_from_extract(extract, case_name, categories)

        print("   extracted", len(new_triples), "triples")
        writer.writerows(new_triples)

caselaw_extraction_template = extraction_template_from_categories(categories)

documents = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)
old_len = len(documents)
documents = documents[:num_docs]
print("using", num_docs, "documents of ", len(documents), "from HF dataset", hf_dataset_id)

with Progress() as progress:

    task_extract = progress.add_task("[green]Extracting entities...", total=len(documents))

    with open(entity_csv_file, "wt") as f:

        writer = csv.writer(f, delimiter=",", quotechar='"')
        writer.writerow(["subject", "predicate", "object"]) # header

        for case_doc in documents:

            display_case(case_doc)
            process_document(caselaw_extraction_template, case_doc, writer)
            progress.update(task_extract, advance=1)

    print("Wrote entity triples to", entity_csv_file)
