
##################################
# Create Vector DB
##################################

embedding_model_id = "all-MiniLM-L6-v2"

embedding_fn = embedding_function(embedding_model_id)
print("Embedding model", embedding_model_id)

db_file_name = Path("milvus.db")

vector_db_client = create_vector_db(db_file_name, embedding_fn) 
print("Vector db stored in file", db_file_name)

##################################
# Add graph nodes to vector db
##################################

from langchain.docstore.document import Document

names = []
with driver.session() as session:
    # Query to find all nodes
    result = session.run("MATCH (n) RETURN n.name AS name")
    for record in result:
        doc = Document(record["name"])
        names.append(doc)

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
print(info['insert_count'], "chunks inserted")
print(vector_db_client.get_collection_stats(collection_name))
print(vector_db_client.describe_collection(collection_name))
