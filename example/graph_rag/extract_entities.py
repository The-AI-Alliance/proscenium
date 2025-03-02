
from rich import print

from .config import num_docs, model_id, hf_dataset_id, hf_dataset_column

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

##################################
# Load documents from HF dataset
##################################

from proscenium.load import load_hugging_face_dataset

documents = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)
print("Document Count: " + str(len(documents)))

print("Truncating to ", num_docs)
documents = documents[:num_docs]

import json

for doc in documents:
    print(json.dumps(doc.metadata, indent=4), "\n")
    print(doc.page_content[:100], "\n")

##################################
# Chunk
##################################

from proscenium.chunk import documents_to_chunks_by_tokens

doc_chunks = {}

for doc in documents:
    id = doc.metadata["id"]
    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    doc_chunks[id] = chunks
    print(f"Case {id} has {len(chunks)} chunks")

# Each text chunk inherits the metadata from the document.
# For the purpose of this recipe, note that the `judge`
# is not well captured in many of these documents;
# we will be extracting it from the case law text.

#import json
#for doc in documents:
#    id = doc.metadata["id"]
#    print(json.dumps(doc.metadata, indent=4))
#    for chunk in doc_chunks[id]:
#        print(chunk.page_content[:100])

##################################
# Extract entities
##################################

from .config import categories
from proscenium.complete import complete_simple
from proscenium.parse import extraction_template

categories_str = "\n".join([f"{k}: {v}" for k, v in categories.items()])

doc_extracts = {}
for doc in documents:
    case_id = doc.metadata['id']
    print(f"\nExtracting entities case id {case_id}")
    extracts = []
    for i, chunk in enumerate(doc_chunks[id]):
        print(f"\nExtracting entities for chunk {i} of case id {case_id}")
        query = extraction_template.format(
            categories = categories_str,
            text = chunk.page_content)
        response = complete_simple(model_id, "You are an entity extractor", query)
        logging.debug(response)
        extracts.append(response)

    doc_extracts[case_id] = extracts

##################################
# Construct triples
##################################

from proscenium.parse import get_triples_from_extract

doc_triples = {}
for doc in documents:
    id = doc.metadata['id']
    name = doc.metadata['name_abbreviation']
    print("TRIPLES FOR id", id, ", name", name)
    triples = []
    for i, extract in enumerate(doc_extracts[id]):
        # Break response up into entity triples.
        new_triples = get_triples_from_extract(extract, name, categories)
        triples.extend(new_triples)
    # Add triples from metadata.
    triples.append((doc.metadata["court"], 'Court', name))

    # Add to triples for the document.
    if id in doc_triples:
        doc_triples[id].append(triples)
    else:
        doc_triples[id] = triples

# Get all of the triples, filtering those that have no entity.
all_triples = []
for case_id, triples in doc_triples.items():
    # print(f"Case {case_id}")
    for triple in triples:
        r = triple[1].lower()
        if "not explicitly mentioned" not in r and "not applicable" not in r and "not specified" not in r:
            all_triples.append(triple)
            logging.debug(triple)


##################################
# Write all_tripes to json file
##################################

import csv
from .config import entity_csv_file

with open(entity_csv_file, "wt") as f:
    writer = csv.writer(f, delimiter=",", quotechar='"')
    writer.writerow(["entity", "role", "case name"]) # header
    writer.writerows(all_triples)

print("Entity triples written to", entity_csv_file)
