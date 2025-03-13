
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
    relations = [record["rel"] for record in result]
    unique_relations = list(set(relations))
    table = Table(title="Relationship Types", show_lines=False)
    table.add_column("Relationship Type", justify="left", style="blue")
    for r in unique_relations:
        table.add_row(r)
    print(table)

    result = session.run("MATCH (n) RETURN n.name AS name") # all nodes
    table = Table(title="Nodes", show_lines=False)
    table.add_column("Node Name", justify="left", style="green")
    for record in result:
        table.add_row(record['name'])
    print(table)

    for r in unique_relations:
        cypher = f"MATCH (s)-[:{r}]->(o) RETURN s.name, o.name"
        result = session.run(cypher)
        table = Table(title=f"Relation: {r}", show_lines=False)
        table.add_column("Subject Name", justify="left", style="blue")
        table.add_column("Object Name", justify="left", style="purple")
        for record in result:
            table.add_row(record['s.name'], record['o.name'])
        print(table)

driver.close()
