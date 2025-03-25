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
import demo.domains.literature as literature_config

os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = typer.Typer()

@app.command(help=f"Build a vector database from chunks of {literature_config.url}.")
def prepare():

    asyncio.run(url_to_file(literature_config.url, literature_config.data_file))
    print("Data file to chunk:", literature_config.data_file)

    embedding_fn = embedding_function(literature_config.embedding_model_id)
    print("Embedding model", literature_config.embedding_model_id)

    vector_db_client = create_vector_db(literature_config.milvus_uri, embedding_fn, overwrite=True)
    print("Vector db at uri", literature_config.milvus_uri)

    bvd(literature_config.data_file, vector_db_client, embedding_fn)

    vector_db_client.close()


@app.command(help="""
Ask a question about literature using the RAG pattern with the chunks prepared in the previous step.
""")
def ask():

    query = literature_config.get_user_question()

    embedding_fn = embedding_function(literature_config.embedding_model_id)
    print("Embedding model:", literature_config.embedding_model_id)

    vector_db_client = vector_db(literature_config.milvus_uri)
    print("Vector db at uri", literature_config.milvus_uri)

    answer = answer_question(query, literature_config.model_id, vector_db_client, embedding_fn)

    print(Panel(answer, title="Assistant"))
