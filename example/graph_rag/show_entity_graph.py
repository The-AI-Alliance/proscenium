
import example.graph_rag.config as config
import example.graph_rag.util as util

from proscenium.know import knowledge_graph_client

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

util.show_entity_graph(driver)

driver.close()
