
from typing import List
from rich import print
import logging
from rich.progress import Progress
from langchain_core.documents.base import Document

from proscenium.read import load_hugging_face_dataset
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.parse import extraction_template
from proscenium.complete import complete_simple
from proscenium.parse import get_triples_from_extract
from proscenium.write import triples_to_csv

from .display import display_case
from .config import entity_csv_file
from .config import categories, categories_str
from .config import model_id
from .config import num_docs, hf_dataset_id, hf_dataset_column

def chunk_to_triples(chunk: Document, case_name: str) -> List[tuple[str, str, str]]:

    query = extraction_template.format(categories = categories_str, text = chunk.page_content)
    extract = complete_simple(model_id, "You are an entity extractor", query)
    new_triples = get_triples_from_extract(extract, case_name, categories)

    return new_triples

def case_to_triples(case_doc: Document) -> List[tuple[str, str, str]]:

    triples = []

    case_name = case_doc.metadata['name_abbreviation']
    display_case(case_doc)

    chunks = documents_to_chunks_by_tokens([case_doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):
        print("chunk", i+1, "of", len(chunks))
        new_triples = chunk_to_triples(chunk, case_name)
        print("   extracted", len(new_triples), "triples")
        triples.extend(new_triples)

    triples.append((case_doc.metadata["court"], 'Court', case_name))

    return triples

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

documents = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)
old_len = len(documents)
documents = documents[:num_docs]
print(old_len, "documents truncated to the first", num_docs)

triples = []

with Progress() as progress:

    task_extract = progress.add_task("[green]Extracting entities...", total=len(documents))

    for case_doc in documents:
        triples.extend(case_to_triples(case_doc))
        progress.update(task_extract, advance=1)

triples_to_csv(triples, entity_csv_file)
print("Wrote", len(triples), "entity triples to", entity_csv_file)
