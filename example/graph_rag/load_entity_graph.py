
from rich import print

from rich.progress import Progress
import csv

from proscenium.know import knowledge_graph_client
from proscenium.display import print_header

import example.graph_rag.config as config

print_header()

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
            for subject, predicate, object in triples:
                session.execute_write(config.add_triple, subject, predicate, object)
                progress.update(task_load, advance=1)

        driver.close()
