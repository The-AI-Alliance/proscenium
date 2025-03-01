
##################
# Configuration
##################

from pathlib import Path

db_file_name = Path("milvus.db")
embedding_model_id = "all-MiniLM-L6-v2"
#model_id = "ollama:llama3.2"
#model_id = "ollama:granite3.1-dense:2b"
model_id = "openai:gpt-4o"

##################
# User Query
##################

query = "What did Hermes say to Prometheus about giving fire to humans?"

##################
# Imports
##################

import os
from rich import print
from rich.panel import Panel
from proscenium.console import print_header
from proscenium.vector_database import display_closest_chunks
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.vector_database import closest_chunks
from proscenium.vector_database import rag_prompt
from proscenium.prompts import rag_system_prompt
from proscenium.inference import complete_simple

##################
# Main
##################

os.environ["TOKENIZERS_PARALLELISM"] = "false"

print_header()

print(Panel(query, title="User"))

embedding_fn = embedding_function(embedding_model_id)
print("Embedding model:", embedding_model_id)

vector_db_client = vector_db(db_file_name, embedding_fn)
print("Connected to vector db stored in", db_file_name)

chunks = closest_chunks(vector_db_client, embedding_fn, query)
print("Found", len(chunks), "closest chunks")
display_closest_chunks(chunks)

prompt = rag_prompt(chunks, query)
print("RAG prompt created. Calling inference at", model_id,"\n\n")

answer = complete_simple(model_id, rag_system_prompt, prompt)
print(Panel(answer, title="Assistant"))
