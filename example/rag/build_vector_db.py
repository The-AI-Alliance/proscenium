
import asyncio
from rich import print

from proscenium.display import header
from proscenium.read import url_to_file
from proscenium.vector_database import embedding_function
from proscenium.vector_database import create_vector_db

import example.rag as rag

print(header())

asyncio.run(url_to_file(rag.config.url, rag.config.data_file))
print("Data file to chunk:", rag.config.data_file)

embedding_fn = embedding_function(rag.config.embedding_model_id)
print("Embedding model", rag.config.embedding_model_id)

vector_db_client = create_vector_db(rag.config.milvus_uri, embedding_fn, overwrite=True)
print("Vector db at uri", rag.config.milvus_uri)

rag.build_vector_db(rag.config.data_file, vector_db_client, embedding_fn)

vector_db_client.close()
