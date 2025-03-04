
from rich import print

import example.graph_rag.config as config

##################################
# Load triples
##################################

import csv

print("Loading triples from", config.entity_csv_file)

with open(config.entity_csv_file) as f:
    reader = csv.reader(f, delimiter=",", quotechar='"')
    next(reader, None)  # skip header row
    triples = [row for row in reader]

##################################
# Connect to Neo4j
##################################

from proscenium.know import knowledge_graph_client

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

##################################
# Populate the graph
##################################

from stringcase import snakecase, lowercase

def add_triple(tx, entity, role, case):
    query = (
        "MERGE (e:Entity {name: $entity}) "
        "MERGE (c:Case {name: $case}) "
        "MERGE (e)-[r:%s]->(c)"
    ) % snakecase(lowercase(role.replace('/', '_')))
    tx.run(query, entity=entity, case=case)

with driver.session() as session:
    session.run("MATCH (n) DETACH DELETE n") # empty graph
    for entity, role, case in triples:
        session.write_transaction(add_triple, entity, role, case)

driver.close()

##################################
# Inspect the graph
##################################

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

with driver.session() as session:
    print("Nodes in the graph:")
    result = session.run("MATCH (n) RETURN n.name AS name") # all nodes
    for record in result:
        print(record["name"])

    print("\nRelationship types in the graph:")
    result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel") # all relationships
    rels = [record["rel"] for record in result]
    rels = list(set(rels)) # unique rels
    for rel in rels:
        print(rel)

    print("Precedents in the graph:")
    result = session.run("MATCH (a)-[:precedent_cited]->() RETURN a.name AS name")
    for record in result:
        print(record["name"])
