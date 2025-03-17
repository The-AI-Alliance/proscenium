
from rich import print

from proscenium.display import header
from proscenium.vector_database import create_vector_db
from proscenium.vector_database import embedding_function
from proscenium.know import knowledge_graph_client
from proscenium.vector_database import collection_name

import example.graph_rag as graph_rag

print(header())

embedding_fn = embedding_function(graph_rag.config.embedding_model_id)
print("Embedding model", graph_rag.config.embedding_model_id)

vector_db_client = create_vector_db(graph_rag.config.milvus_uri, embedding_fn, overwrite=True)
print("Vector db stored at", graph_rag.config.milvus_uri)

driver = knowledge_graph_client(
    graph_rag.config.neo4j_uri,
    graph_rag.config.neo4j_username,
    graph_rag.config.neo4j_password)

graph_rag.load_entity_resolver(driver, vector_db_client, embedding_fn, collection_name)

driver.close()
vector_db_client.close()
