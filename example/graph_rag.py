
from rich import print

# Taken from python notebook on a branch:
# https://github.com/ibm-granite-community/granite-legal-cookbook/blob/158-legal-graph-rag/recipes/Graph/Entity_Extraction_from_NH_Caselaw.ipynb

##################################
# Model
##################################

model_id = "openai:gpt-4o"

##################################
# Load documents from HF dataset
##################################

from proscenium.load import load_hugging_face_dataset

documents = load_hugging_face_dataset("free-law/nh", page_content_column="text")
print("Document Count: " + str(len(documents)))

num_docs = 10

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

categories = {
    "Judge/Justice": "The name of the judge or justice involved in the case, including their role (e.g., trial judge, appellate judge, presiding justice).",
    "Precedent Cited": "Previous case law referred to in the case.",
}

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
for id, triples in doc_triples.items():
    print(f"Case {id}")
    for triple in triples:
        r = triple[1].lower()
        if "not explicitly mentioned" not in r and "not applicable" not in r and "not specified" not in r:
            all_triples.append(triple)
            print(triple)

import sys
sys.exit(0)

##################################
# Populate the graph
##################################

from neo4j import GraphDatabase
from stringcase import snakecase, lowercase

# Define the list of (entity, relationship, entity) triples
triples = all_triples

# TODO neo4j setup instructions

# Connect to the Neo4j database
uri = get_env_var("NEO4J_URI")
username = get_env_var("NEO4J_USERNAME")
password = get_env_var("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(username, password))

def add_triple(tx, entity, role, case):
    query = (
        "MERGE (e:Entity {name: $entity}) "
        "MERGE (c:Case {name: $case}) "
        "MERGE (e)-[r:%s]->(c)"
    ) % snakecase(lowercase(role.replace('/', '_')))
    tx.run(query, entity=entity, case=case)

def build_graph(triples):
    with driver.session() as session:
        # Empty the graph first
        session.run("MATCH (n) DETACH DELETE n")
        # Fill the graph
        for entity, role, case in triples:
            session.write_transaction(add_triple, entity, role, case)

# Build the graph from the triples list
build_graph(triples)

# Close the connection to the database
driver.close()


##################################
# Inspect the graph
##################################

with driver.session() as session:
    # Query to find all nodes
    result = session.run("MATCH (n) RETURN n.name AS name")
    print("Nodes in the graph:")
    for record in result:
        print(record["name"])

    # Query to find all relationships
    result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel")
    print("\nRelationship types in the graph:")
    rels = [record["rel"] for record in result]
    # unique rels
    rels = list(set(rels))
    for rel in rels:
        print(rel)

##################################
# Find cited precedents
##################################

driver = GraphDatabase.driver(uri, auth=(username, password))
with driver.session() as session:
    # Query to find all nodes
    result = session.run("MATCH (a)-[:precedent_cited]->() RETURN a.name AS name")
    print("Precedents in the graph:")
    for record in result:
        print(record["name"])

##################################
# Create Vector DB
##################################

embedding_model_id = "all-MiniLM-L6-v2"

embedding_fn = embedding_function(embedding_model_id)
print("Embedding model", embedding_model_id)

db_file_name = Path("milvus.db")

vector_db_client = create_vector_db(db_file_name, embedding_fn) 
print("Vector db stored in file", db_file_name)

##################################
# Add graph nodes to vector db
##################################

from langchain.docstore.document import Document

names = []
with driver.session() as session:
    # Query to find all nodes
    result = session.run("MATCH (n) RETURN n.name AS name")
    for record in result:
        doc = Document(record["name"])
        names.append(doc)

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
print(info['insert_count'], "chunks inserted")
print(vector_db_client.get_collection_stats(collection_name))
print(vector_db_client.describe_collection(collection_name))

##################################
# Extract entities from question
##################################

question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"

response = complete_simple(model_id, "You are an entity extractor", extraction_template.format(
    categories = categories_str,
    text = question))
print(response)

extraction_entity_triples = get_triples_from_extract(response, "")
print(question_entity_triples)

##################################
# Match entities to graph
##################################

from proscenium.vector_database import closest_chunks

def match_entity(name, threshold=1.0):

    """Match entities by embedding vector distance given a similarity threshold."""

    hits = closest_chunks(vector_db_client, embedding_fn, name, k=5)
    # TODO print the hits
    if len(hits) > 0:
        # TODO confirm that 0th element is the closest match
        hit = hits[0]
        if hit['distance'] <= threshold:
            return hit['entity']['text']
    else:
        return None

for triple in question_entity_triples:
    name = triple[0]
    print(f"\nMatching {name}")
    match = match_entity(name)
    if match is not None:
        print(f"Match: {match}")

##################################
# Query graph for cases
##################################

def query_for_cases(entity_name, role):
    with driver.session() as session:
        relationship = snakecase(lowercase(role.replace('/', '_')))
        query = f"MATCH (e:Entity {{name: '{entity_name}'}})-[:{relationship}]->(c:Case) RETURN c.name AS name"
        print(query)
        result = session.run(query)
        print("Cases:")
        for record in result:
            print(record["name"])

for triple in question_entity_triples:
    entity, role, case = triple
    entity_match = match_entity(entity)
    query_for_cases(entity_match, role)

##################################
# Query for cases given multiple entities and their relationships to the case.
##################################

def query_for_cases(entity_role_pairs):
    with driver.session() as session:
        query = ""
        for i, (entity, role) in enumerate(entity_role_pairs):
            relationship = snakecase(lowercase(role.replace('/', '_')))
            query += f"MATCH (e{str(i)}:Entity {{name: '{entity}'}})-[:{relationship}]->(c)\n"
        query += "RETURN c.name AS name"
        print(query)
        result = session.run(query)
        cases = []
        print("Cases:")
        for record in result:
            cases.append(record["name"])
            print(record["name"])
        return cases

entity_role_pairs = []
for triple in question_entity_triples:
    entity, role, case = triple
    entity_match = match_entity(entity)
    entity_role_pairs.append((entity_match, role))
    
cases = query_for_cases(entity_role_pairs)

##################################
# Retrieve case text
##################################

case_text = [doc.page_content for doc in documents if doc.metadata["name_abbreviation"] == cases[0]][0]
print(case_text)

##################################
# Answer question
##################################

query_template = """
Answer the question using the following text from one case: \n\n{case_text}

Question: {question}
"""

query = query_template.format(
    case_text = case_text,
    question = question)
print(query)

response = complete_simple(model_id, "You are a helpful law librarian", query)
print(response)
