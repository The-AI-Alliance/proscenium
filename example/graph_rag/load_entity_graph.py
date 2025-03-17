
from rich import print

from proscenium.know import knowledge_graph_client
from proscenium.display import header

import example.graph_rag as graph_rag

print(header())

driver = knowledge_graph_client(
    graph_rag.config.neo4j_uri,
    graph_rag.config.neo4j_username,
    graph_rag.config.neo4j_password)

graph_rag.load_entity_graph(
    driver,
    graph_rag.config.entity_csv_file,
    graph_rag.config.add_triple)

driver.close()
