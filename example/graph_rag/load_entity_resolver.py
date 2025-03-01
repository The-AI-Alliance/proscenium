
from rich import print

##################################
# Create Vector DB
##################################

from pathlib import Path
from .config import embedding_model_id, milvus_db_file
from proscenium.vector_database import create_vector_db
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import embedding_function

embedding_fn = embedding_function(embedding_model_id)
print("Embedding model", embedding_model_id)

db_file_name = Path(milvus_db_file)

vector_db_client = create_vector_db(db_file_name, embedding_fn) 
print("Vector db stored in file", db_file_name)

##################################
# Connect to Neo4j
##################################

import os
uri = os.environ["NEO4J_URI"] = "bolt://localhost:7687"
username = os.environ["NEO4J_USERNAME"] = "neo4j"
password = os.environ["NEO4J_PASSWORD"] = "password"

from neo4j import GraphDatabase
driver = GraphDatabase.driver(uri, auth=(username, password))

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
