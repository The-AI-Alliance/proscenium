
import os
from rich import print
from rich.panel import Panel

from proscenium.display import header
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db

import example.rag.util as util
import example.rag.config as config

os.environ["TOKENIZERS_PARALLELISM"] = "false"

print(header())

query = config.get_user_question()

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model:", config.embedding_model_id)

vector_db_client = vector_db(config.milvus_uri)
print("Vector db at uri", config.milvus_uri)

answer = util.answer_question(query, config.model_id, vector_db_client, embedding_fn)
print(Panel(answer, title="Assistant"))
