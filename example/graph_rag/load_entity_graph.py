
from rich import print

from rich.progress import Progress
from stringcase import snakecase, lowercase
import csv

from proscenium.know import knowledge_graph_client

import example.graph_rag.config as config

def add_triple(tx, entity, role, case):
    query = (
        "MERGE (e:Entity {name: $entity}) "
        "MERGE (c:Case {name: $case}) "
        "MERGE (e)-[r:%s]->(c)"
    ) % snakecase(lowercase(role.replace('/', '_')))
    tx.run(query, entity=entity, case=case)

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
