import typer
import os
from rich import print
from rich.panel import Panel
import asyncio

from proscenium.read import url_to_file
from proscenium.vector_database import embedding_function
from proscenium.vector_database import create_vector_db
from proscenium.vector_database import vector_db

from example.rag import answer_question, build_vector_db as bvd

import example.rag.config as config


os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = typer.Typer()

@app.command()
def build_vector_db():

    asyncio.run(url_to_file(config.url, config.data_file))
    print("Data file to chunk:", config.data_file)

    embedding_fn = embedding_function(config.embedding_model_id)
    print("Embedding model", config.embedding_model_id)

    vector_db_client = create_vector_db(config.milvus_uri, embedding_fn, overwrite=True)
    print("Vector db at uri", config.milvus_uri)

    bvd(config.data_file, vector_db_client, embedding_fn)

    vector_db_client.close()


@app.command()
def ask():

    query = config.get_user_question()

    embedding_fn = embedding_function(config.embedding_model_id)
    print("Embedding model:", config.embedding_model_id)

    vector_db_client = vector_db(config.milvus_uri)
    print("Vector db at uri", config.milvus_uri)

    answer = answer_question(query, config.model_id, vector_db_client, embedding_fn)

    print(Panel(answer, title="Assistant"))
