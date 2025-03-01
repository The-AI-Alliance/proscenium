
from rich import print

from .config import num_docs, model_id, hf_dataset_id, hf_dataset_column

##################################
# Load documents from HF dataset
##################################

from proscenium.load import load_hugging_face_dataset

documents = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)
print("Document Count: " + str(len(documents)))

print("Truncating to ", num_docs)
documents = documents[:num_docs]

##################################
# Filter documents
##################################

# if doc.metadata["id"] in ['4440632', '4441078']]

##################################
# Inspect documents
##################################

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

##################################
# Inspect chunks
##################################

# Each text chunk inherits the metadata from the document.
# For the purpose of this recipe, note that the `judge`
# is not well captured in many of these documents;
# we will be extracting it from the case law text.

import json
for doc in documents:
    id = doc.metadata["id"]
    print(json.dumps(doc.metadata, indent=4))
    for chunk in doc_chunks[id]:
        print(chunk.page_content[:100])

##################################
# Extracting entities
##################################

from proscenium.inference import complete_simple
from .config import categories

extraction_template = """\
Below is a list of entity categories:

{categories}

Given this list of entity categories, you will be asked to extract entities belonging to these categories from a text passage.
Consider only the list of entity categories above; do not extract any additional entities.
For each entity found, list the category and the entity, separated by a semicolon.
Do not use the words "Entity" or "Category".

Find the entities in the following text, and list them in the format specified above:

{text}
"""

categories_str = "\n".join([f"{k}: {v}" for k, v in categories.items()])

doc_extracts = {}
for doc in documents:
    id = doc.metadata['id']
    extracts = []
    for i, chunk in enumerate(doc_chunks[id]):
        print(f"\nChunk {i} of {id}")
        query = extraction_template.format(
            categories = categories_str,
            text = chunk.page_content)
        print(str(len(query)) + " characters in query")
        response = complete_simple(model_id, "You are an entity extractor", query)
        print(response)
        extracts.append(response)

    doc_extracts[id] = extracts

##################################
# Construct graph triples
##################################

def get_triples_from_extract(extract, case_name):
    triples = []
    lines = extract.splitlines()
    for line in lines:
        try:
            # Take the number off of the front.
            line = line.split(". ", 1)[1]
            role, entity = line.split(": ", 2)
            if role in categories:
                triple = (entity, role, case_name)
                triples.append(triple)
        except (ValueError, IndexError):
            print(f"Error parsing case {id} line: {line}")
    return triples

doc_triples = {}
for doc in documents:
    id = doc.metadata['id']
    name = doc.metadata['name_abbreviation']
    triples = []
    for i, extract in enumerate(doc_extracts[id]):
        # Break response up into entity triples.
        new_triples = get_triples_from_extract(extract, name);
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
    print(f"Case {case_id}")
    for triple in triples:
        r = triple[1].lower()
        if "not explicitly mentioned" not in r and "not applicable" not in r and "not specified" not in r:
            all_triples.append(triple)
            print(triple)
