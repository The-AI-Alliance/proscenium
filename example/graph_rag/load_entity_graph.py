
from rich import print

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

# Define the list of (entity, relationship, entity) triples
triples = all_triples

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

with driver.session() as session:
    # Query to find all nodes
    result = session.run("MATCH (a)-[:precedent_cited]->() RETURN a.name AS name")
    print("Precedents in the graph:")
    for record in result:
        print(record["name"])
