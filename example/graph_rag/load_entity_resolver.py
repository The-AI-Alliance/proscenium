
from rich import print

from langchain.docstore.document import Document

from proscenium.vector_database import create_vector_db
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import embedding_function
from proscenium.know import knowledge_graph_client
from proscenium.vector_database import collection_name

import example.graph_rag.config as config

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model", config.embedding_model_id)

vector_db_client = create_vector_db(config.milvus_db_file, embedding_fn, overwrite=True)
print("Vector db stored in file", config.milvus_db_file)

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

names = []
with driver.session() as session:
    result = session.run("MATCH (n) RETURN n.name AS name")
    for record in result:
        doc = Document(record["name"])
        names.append(doc)

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, names)
print(info['insert_count'], "chunks inserted")
print("Collection row count:", vector_db_client.get_collection_stats(collection_name)['row_count'])
# print(vector_db_client.describe_collection(collection_name))
