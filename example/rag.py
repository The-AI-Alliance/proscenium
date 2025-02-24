
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
import logging
from rich import print
from proscenium.console import print_header
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.vector_database import closest_chunks
from proscenium.vector_database import rag_prompt
from proscenium.prompts import rag_system_prompt
from proscenium.inference import complete_simple

##################
# Utilities
##################

from rich.table import Table
def display_closest_chunks(
    chunks: list[dict]
):
    table = Table(title="Closest Chunks", show_lines=True)
    table.add_column("id", justify="right", style="cyan")
    table.add_column("distance", style="magenta")
    table.add_column("entity.text", justify="right", style="green")
    for chunk in chunks:
        table.add_row(str(chunk['id']), str(chunk['distance']), chunk['entity']['text'])
    print(table)

##################
# Main
##################

os.environ["TOKENIZERS_PARALLELISM"] = "false"

print_header()

print("USER\n", query, "\n")

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
print("ASSISTANT\n", answer, "\n")
