
from rich import print

from langchain.docstore.document import Document

from proscenium.display import header
from proscenium.vector_database import create_vector_db
from proscenium.vector_database import embedding_function
from proscenium.know import knowledge_graph_client
from proscenium.vector_database import collection_name

import example.graph_rag.config as config
import example.graph_rag.util as util

print(header())

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model", config.embedding_model_id)

vector_db_client = create_vector_db(config.milvus_uri, embedding_fn, overwrite=True)
print("Vector db stored at", config.milvus_uri)

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

util.load_entity_resolver(driver, vector_db_client, embedding_fn, collection_name)
