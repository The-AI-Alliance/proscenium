import typer
import os
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
import asyncio

from proscenium.verbs.read import url_to_file
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.rag import answer_question
from proscenium.scripts.chunk_space import build_vector_db as bvd
import demo.domains.literature as domain

collection_name = "literature_chunks"

default_milvus_uri = "file:/milvus.db"
# milvus_uri = "http://localhost:19530"

os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = typer.Typer(
    help="""Question answering using RAG on a text from the Gutenberg Project."""
)


@app.command(
    help=f"""Build a vector DB from chunks of {len(domain.books)} books from Project Gutenberg.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def prepare():

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    for book in domain.books:
        print("Book:", book.title)
        asyncio.run(url_to_file(book.url, book.data_file))
        print("Local copy to chunk:", book.data_file)

    embedding_fn = embedding_function(domain.embedding_model_id)
    print("Embedding model", domain.embedding_model_id)

    vector_db_client = vector_db(milvus_uri, overwrite=True)
    print("Vector db at uri", milvus_uri)

    bvd(
        [str(book.data_file) for book in domain.books],
        vector_db_client,
        embedding_fn,
        collection_name,
    )

    vector_db_client.close()


@app.command(
    help="""
Ask a question about literature using the RAG pattern with the chunks prepared in the previous step.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def ask(loop: bool = False, question: str = None, verbose: bool = False):

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    while True:

        if question is None:
            q = Prompt.ask(
                domain.user_prompt,
                default=domain.default_question,
            )
        else:
            q = question

        vector_db_client = vector_db(milvus_uri)
        print("Vector db at uri", milvus_uri)

        embedding_fn = embedding_function(domain.embedding_model_id)
        print("Embedding model:", domain.embedding_model_id)

        answer = answer_question(
            q, domain.model_id, vector_db_client, embedding_fn, collection_name, verbose
        )

        print(Panel(answer, title="Assistant"))

        if loop:
            question = None
        else:
            break
