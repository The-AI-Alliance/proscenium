import typer
import logging
import os

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import demo.domains.literature as domain

default_milvus_uri = "file:/milvus.db"
# milvus_uri = "http://localhost:19530"
milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

collection_name = "literature_chunks"

os.environ["TOKENIZERS_PARALLELISM"] = "false"

app = typer.Typer(
    help="""Question answering using RAG on a text from the Gutenberg Project."""
)

console = Console()


@app.command(
    help=f"""Build a vector DB from chunks of {len(domain.books)} books from Project Gutenberg.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def prepare(verbose: bool = False):

    sub_console = None
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        sub_console = Console()

    build = domain.make_chunk_space_builder(
        milvus_uri,
        collection_name,
        domain.default_embedding_model_id,
        console=sub_console,
    )
    console.print("Building chunk space")
    build(force=True)


@app.command(
    help="""
Ask a question about literature using the RAG pattern with the chunks prepared in the previous step.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def ask(loop: bool = False, question: str = None, verbose: bool = False):

    sub_console = None
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        sub_console = Console()

    handle = domain.make_handler(
        domain.default_generator_model_id,
        milvus_uri,
        domain.default_embedding_model_id,
        console=sub_console,
    )

    while True:

        if question is None:
            q = Prompt.ask(
                domain.user_prompt,
                default=domain.default_question,
            )
        else:
            q = question

        for answer in handle(q):
            console.print(Panel(answer, title="Assistant"))

        if loop:
            question = None
        else:
            break
