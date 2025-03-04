
from rich import print

import example.graph_rag.config as config

##################################
# Create Vector DB
##################################

from proscenium.vector_database import create_vector_db
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import embedding_function

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model", config.embedding_model_id)

vector_db_client = create_vector_db(config.milvus_db_file, embedding_fn) 
print("Vector db stored in file", config.milvus_db_file)

##################################
# Connect to Neo4j
##################################

from proscenium.know import knowledge_graph_client

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

##################################
# Add graph nodes to vector db
##################################

from langchain.docstore.document import Document
from proscenium.vector_database import collection_name

names = []
with driver.session() as session:
    result = session.run("MATCH (n) RETURN n.name AS name")
    for record in result:
        doc = Document(record["name"])
        names.append(doc)

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, names)
print(info['insert_count'], "chunks inserted")
print(vector_db_client.get_collection_stats(collection_name))
print(vector_db_client.describe_collection(collection_name))
