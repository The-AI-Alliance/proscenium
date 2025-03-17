
import asyncio
from rich import print

from proscenium.display import header
from proscenium.read import url_to_file
from proscenium.vector_database import embedding_function
from proscenium.vector_database import create_vector_db

import example.rag.config as config
import example.rag.util as util

print(header())

asyncio.run(url_to_file(config.url, config.data_file))
print("Data file to chunk:", config.data_file)

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model", config.embedding_model_id)

vector_db_client = create_vector_db(config.milvus_uri, embedding_fn, overwrite=True)
print("Vector db at uri", config.milvus_uri)

util.build_vector_db(config.data_file, vector_db_client, embedding_fn)

vector_db_client.close()
