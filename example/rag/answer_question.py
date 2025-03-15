
query = "What did Hermes say to Prometheus about giving fire to humans?"

import os
from rich import print
from rich.panel import Panel

from proscenium.display import header
from proscenium.display.milvus import chunk_hits_table
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.vector_database import closest_chunks
from proscenium.complete import complete_simple

from .prompts import rag_system_prompt, rag_prompt
import example.rag.config as config

os.environ["TOKENIZERS_PARALLELISM"] = "false"

print(header())

print(Panel(query, title="User"))

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model:", config.embedding_model_id)

#vector_db_client = vector_db(db_file_name, embedding_fn)
#print("Connected to vector db stored in", db_file_name)
vector_db_client = vector_db(config.milvus_uri)
print("Vector db at uri", config.milvus_uri)

chunks = closest_chunks(vector_db_client, embedding_fn, query)
print("Found", len(chunks), "closest chunks")
print(chunk_hits_table(chunks))

prompt = rag_prompt(chunks, query)
print("RAG prompt created. Calling inference at", config.model_id,"\n\n")

answer = complete_simple(config.model_id, rag_system_prompt, prompt)
print(Panel(answer, title="Assistant"))
