

import asyncio
from rich import print

from proscenium.display import print_header
from proscenium.surf import url_to_file
from proscenium.vector_database import embedding_function
from proscenium.vector_database import create_vector_db
from proscenium.load import load_file
from proscenium.chunk import documents_to_chunks_by_characters
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import collection_name

from .config import db_file_name, embedding_model_id, url, data_file

print_header()

asyncio.run(url_to_file(url, data_file))
print("Data files to chunk:", data_file)

embedding_fn = embedding_function(embedding_model_id)
print("Embedding model", embedding_model_id)

if db_file_name.exists():
    db_file_name.unlink()
    print("Deleted existing vector db file", db_file_name)
vector_db_client = create_vector_db(db_file_name, embedding_fn) 
print("Vector db stored in file", db_file_name)

documents = load_file(data_file)
chunks = documents_to_chunks_by_characters(documents)
print("Data file", data_file, "has", len(chunks), "chunks")

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
print(info['insert_count'], "chunks inserted")
print(vector_db_client.get_collection_stats(collection_name))

print(vector_db_client.describe_collection(collection_name))
