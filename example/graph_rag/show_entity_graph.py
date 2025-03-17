
import example.graph_rag as graph_rag

from proscenium.know import knowledge_graph_client

driver = knowledge_graph_client(
    graph_rag.config.neo4j_uri,
    graph_rag.config.neo4j_username,
    graph_rag.config.neo4j_password)

graph_rag.show_entity_graph(driver)

driver.close()
