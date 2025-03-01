
from rich import print

question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"

##################################
# Extract entities from question
##################################

from proscenium.inference import complete_simple
from .config import model_id, categories

categories_str = "\n".join([f"{k}: {v}" for k, v in categories.items()])

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
from proscenium.console import display_chunk_hits

def match_entity(name, threshold=1.0):

    """Match entities by embedding vector distance given a similarity threshold."""

    hits = closest_chunks(vector_db_client, embedding_fn, name, k=5)
    display_chunk_hits(hits)

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
# Connect to Neo4j
##################################

import os
uri = os.environ["NEO4J_URI"] = "bolt://localhost:7687"
username = os.environ["NEO4J_USERNAME"] = "neo4j"
password = os.environ["NEO4J_PASSWORD"] = "password"

from neo4j import GraphDatabase
driver = GraphDatabase.driver(uri, auth=(username, password))


##################################
# Query graph for cases
##################################

from stringcase import snakecase, lowercase

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
