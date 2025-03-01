
query = "What did Hermes say to Prometheus about giving fire to humans?"

import os
from rich import print
from rich.panel import Panel

from proscenium.display import print_header
from proscenium.display import display_chunk_hits
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.vector_database import closest_chunks
from proscenium.complete import complete_simple

from .prompts import rag_system_prompt
from .prompts import rag_prompt
from .config import db_file_name, model_id, embedding_model_id

os.environ["TOKENIZERS_PARALLELISM"] = "false"

print_header()

print(Panel(query, title="User"))

embedding_fn = embedding_function(embedding_model_id)
print("Embedding model:", embedding_model_id)

vector_db_client = vector_db(db_file_name, embedding_fn)
print("Connected to vector db stored in", db_file_name)

chunks = closest_chunks(vector_db_client, embedding_fn, query)
print("Found", len(chunks), "closest chunks")
display_chunk_hits(chunks)

from .prompts import rag_prompt_template

prompt = rag_prompt(chunks, query)
print("RAG prompt created. Calling inference at", model_id,"\n\n")

answer = complete_simple(model_id, rag_system_prompt, prompt)
print(Panel(answer, title="Assistant"))
