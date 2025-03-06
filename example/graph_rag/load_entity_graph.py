
from rich import print
<<<<<<< HEAD

##################################
# Load triples
##################################

import json
from .config import entity_json_file

with open(entity_json_file) as infile:
    triples = json.load(infile)

##################################
# Connect to Neo4j
##################################

from .config import neo4j_uri, neo4j_username, neo4j_password
from proscenium.know import knowledge_graph_client

driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

##################################
# Populate the graph
##################################

from stringcase import snakecase, lowercase
=======
from rich.progress import Progress
from stringcase import snakecase, lowercase
import csv

from proscenium.know import knowledge_graph_client

import example.graph_rag.config as config
>>>>>>> main

def add_triple(tx, entity, role, case):
    query = (
        "MERGE (e:Entity {name: $entity}) "
        "MERGE (c:Case {name: $case}) "
        "MERGE (e)-[r:%s]->(c)"
    ) % snakecase(lowercase(role.replace('/', '_')))
    tx.run(query, entity=entity, case=case)

<<<<<<< HEAD
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

with driver.session() as session:
    # Query to find all nodes
    result = session.run("MATCH (a)-[:precedent_cited]->() RETURN a.name AS name")
    print("Precedents in the graph:")
    for record in result:
        print(record["name"])
=======
print("Parsing triples from", config.entity_csv_file)

with open(config.entity_csv_file) as f:
    reader = csv.reader(f, delimiter=",", quotechar='"')
    next(reader, None)  # skip header row
    triples = [row for row in reader]

    with Progress() as progress:

        task_load = progress.add_task(f"[green]Loading {len(triples)} triples into graph...", total=len(triples))

        driver = knowledge_graph_client(
            config.neo4j_uri,
            config.neo4j_username,
            config.neo4j_password)


        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n") # empty graph
            for entity, role, case in triples:
                session.execute_write(add_triple, entity, role, case)
                progress.update(task_load, advance=1)

        driver.close()
>>>>>>> main
