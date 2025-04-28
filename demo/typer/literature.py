import typer
import os
from rich import print
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


@app.command(
    help=f"""Build a vector DB from chunks of {len(domain.books)} books from Project Gutenberg.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def prepare(verbose: bool = False):

    build = domain.make_chunk_space_builder(
        milvus_uri, collection_name, domain.default_embedding_model_id, verbose
    )
    print("Building chunk space")
    build(force=True)


@app.command(
    help="""
Ask a question about literature using the RAG pattern with the chunks prepared in the previous step.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def ask(loop: bool = False, question: str = None, verbose: bool = False):

    handle = domain.make_handler(
        domain.default_generator_model_id,
        milvus_uri,
        domain.default_embedding_model_id,
        verbose,
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
            print(Panel(answer, title="Assistant"))

        if loop:
            question = None
        else:
            break
