import typer
import os
from rich import print
from rich.panel import Panel
import asyncio

from proscenium.verbs.read import url_to_file
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import create_vector_db
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.rag import answer_question, build_vector_db as bvd
from proscenium.typer import rag_config

os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = typer.Typer()

@app.command()
def build_vector_db():

    asyncio.run(url_to_file(rag_config.url, rag_config.data_file))
    print("Data file to chunk:", rag_config.data_file)

    embedding_fn = embedding_function(rag_config.embedding_model_id)
    print("Embedding model", rag_config.embedding_model_id)

    vector_db_client = create_vector_db(rag_config.milvus_uri, embedding_fn, overwrite=True)
    print("Vector db at uri", rag_config.milvus_uri)

    bvd(rag_config.data_file, vector_db_client, embedding_fn)

    vector_db_client.close()


@app.command()
def ask():

    query = rag_config.get_user_question()

    embedding_fn = embedding_function(rag_config.embedding_model_id)
    print("Embedding model:", rag_config.embedding_model_id)

    vector_db_client = vector_db(rag_config.milvus_uri)
    print("Vector db at uri", rag_config.milvus_uri)

    answer = answer_question(query, rag_config.model_id, vector_db_client, embedding_fn)

    print(Panel(answer, title="Assistant"))
