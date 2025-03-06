
from rich import print
from rich.table import Table

import example.graph_rag.config as config

from proscenium.know import knowledge_graph_client

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

with driver.session() as session:

    result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel") # all relationships
    rels = [record["rel"] for record in result]
    rels = list(set(rels)) # unique rels
    table = Table(title="Relationship Types", show_lines=False)
    table.add_column("Relationship Type", justify="left", style="blue")
    for record in rels:
        table.add_row(record)
    print(table)

    result = session.run("MATCH (n) RETURN n.name AS name") # all nodes
    table = Table(title="Nodes", show_lines=False)
    table.add_column("Node Name", justify="left", style="green")
    for record in result:
        table.add_row(record['name'])
    print(table)

    result = session.run("MATCH (a)-[:precedent_cited]->() RETURN a.name AS name")
    table = Table(title="Cited Precedents", show_lines=False)
    table.add_column("Precedent Name", justify="left", style="blue")
    for record in result:
        table.add_row(record['name'])
    print(table)

driver.close()
