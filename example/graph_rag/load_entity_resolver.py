
from rich import print

from langchain.docstore.document import Document

from proscenium.display import header
from proscenium.vector_database import create_vector_db
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import embedding_function
from proscenium.know import knowledge_graph_client
from proscenium.vector_database import collection_name
from proscenium.display import collection_panel

import example.graph_rag.config as config

print(header())

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model", config.embedding_model_id)

vector_db_client = create_vector_db(config.milvus_uri, embedding_fn, overwrite=True)
print("Vector db stored at", config.milvus_uri)

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

names = []
with driver.session() as session:
    result = session.run("MATCH (n) RETURN n.name AS name")
    new_names = [Document(record["name"]) for record in result]
    names.extend(new_names)

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, names)
print(info['insert_count'], "chunks inserted")
print(collection_panel(vector_db_client, collection_name))
