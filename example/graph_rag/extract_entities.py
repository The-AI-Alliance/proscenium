from rich import print
from rich.panel import Panel
from .config import num_docs, model_id, hf_dataset_id, hf_dataset_column

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

##################################
# Load documents from HF dataset
##################################

from proscenium.load import load_hugging_face_dataset
from .display import display_case

documents = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)
print("Document Count: " + str(len(documents)))

print("Truncating to the first", num_docs)
documents = documents[:num_docs]

for doc in documents:
    display_case(doc)

##################################
# Chunk
##################################

# Each text chunk inherits the metadata from the document.

from proscenium.chunk import documents_to_chunks_by_tokens

print(Panel("Chunking"))

doc_chunks = {}
for doc in documents:
    case_id = doc.metadata['id']
    name = doc.metadata['name_abbreviation']
    print("case", case_id, name)
    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    print("   ", len(chunks), "chunks")
    doc_chunks[case_id] = chunks

##################################
# Extract entities
##################################

# For the purpose of this recipe, note that the `judge`
# is not well captured in many of these documents;
# we will be extracting it from the case law text.

from .config import categories
from proscenium.complete import complete_simple
from proscenium.parse import extraction_template

print(Panel("Extracting entities"))

categories_str = "\n".join([f"{k}: {v}" for k, v in categories.items()])

def chunk_to_extract(chunk: str):

    query = extraction_template.format(
        categories = categories_str,
        text = chunk.page_content)

    response = complete_simple(model_id, "You are an entity extractor", query)
    logging.debug(response)
    return response

doc_extracts = {}
for doc in documents:
    case_id = doc.metadata['id']
    name = doc.metadata['name_abbreviation']
    print("case", case_id, name)
    extracts = []
    for i, chunk in enumerate(doc_chunks[case_id]):
        print("   chunk", i)
        extract = chunk_to_extract(chunk)
        extracts.append(extract)

    doc_extracts[case_id] = extracts

##################################
# Construct triples
##################################

from proscenium.parse import get_triples_from_extract

print(Panel("Parsing extracts"))

triples = []
for doc in documents:
    case_id = doc.metadata['id']
    name = doc.metadata['name_abbreviation']
    print("case", case_id, name)
    extracts = doc_extracts[case_id]
    for extract in extracts:
        new_triples = get_triples_from_extract(extract, name, categories)
        triples.extend(new_triples)
    triples.append((doc.metadata["court"], 'Court', name))

##################################
# Write triples to json file
##################################

import csv
from .config import entity_csv_file

print(Panel("Writing CSV"))

with open(entity_csv_file, "wt") as f:
    writer = csv.writer(f, delimiter=",", quotechar='"')
    writer.writerow(["entity", "role", "case name"]) # header
    writer.writerows(triples)

print(len(triples), "entity triples written to", entity_csv_file)
