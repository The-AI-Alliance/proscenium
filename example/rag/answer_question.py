
import os
from rich import print
from rich.panel import Panel

from proscenium.display import header
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db

import example.rag as rag

os.environ["TOKENIZERS_PARALLELISM"] = "false"

print(header())

query = rag.config.get_user_question()

embedding_fn = embedding_function(rag.config.embedding_model_id)
print("Embedding model:", rag.config.embedding_model_id)

vector_db_client = vector_db(rag.config.milvus_uri)
print("Vector db at uri", rag.config.milvus_uri)

answer = rag.answer_question(query, rag.config.model_id, vector_db_client, embedding_fn)

print(Panel(answer, title="Assistant"))
