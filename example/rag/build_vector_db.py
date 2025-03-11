

import asyncio
from rich import print

from proscenium.display import print_header
from proscenium.read import url_to_file
from proscenium.vector_database import embedding_function
from proscenium.vector_database import create_vector_db
from proscenium.read import load_file
from proscenium.chunk import documents_to_chunks_by_characters
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import collection_name

import example.rag.config as config

print_header()

asyncio.run(url_to_file(config.url, config.data_file))
print("Data files to chunk:", config.data_file)

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model", config.embedding_model_id)

vector_db_client = create_vector_db(config.milvus_uri, embedding_fn, overwrite=True)
print("Vector db at uri", config.milvus_uri)

documents = load_file(config.data_file)
chunks = documents_to_chunks_by_characters(documents)
print("Data file", config.data_file, "has", len(chunks), "chunks")

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
print(info['insert_count'], "chunks inserted")
print(vector_db_client.get_collection_stats(collection_name))
print(vector_db_client.describe_collection(collection_name))
