
import logging
from rich import print
from rich.panel import Panel

from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.know import knowledge_graph_client
from proscenium.display import header

import example.graph_rag.util as util
import example.graph_rag.config as config

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

print(header())

embedding_fn = embedding_function(config.embedding_model_id)
vector_db_client = vector_db(config.milvus_uri)
print("Connected to vector db stored at", config.milvus_uri, "with embedding model", config.embedding_model_id)
print("\n")

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

question = config.get_user_question()
answer = util.answer_question(question, driver, vector_db_client, embedding_fn)
if answer:
    print(Panel(answer, title="Answer"))
else:
    print("No objects found for entity role pairs")
