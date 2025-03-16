
from rich import print

from proscenium.know import knowledge_graph_client
from proscenium.display import header

import example.graph_rag.config as config
import example.graph_rag.util as util

print(header())

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

util.load_entity_graph(config.entity_csv_file)
