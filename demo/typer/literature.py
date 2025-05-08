import typer
import logging
import os

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

from demo.scenes import literature

log = logging.getLogger(__name__)

console = Console()

collection_name = "literature_chunks"

os.environ["TOKENIZERS_PARALLELISM"] = "false"

default_milvus_uri = "file:/milvus.db"
# milvus_uri = "http://localhost:19530"
milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

app = typer.Typer(
    help="""Question answering using RAG on a text from the Gutenberg Project."""
)


@app.command(
    help=f"""Build a vector DB from chunks of {len(literature.books)} books from Project Gutenberg.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def prepare(verbose: bool = False):

    sub_console = None
    if verbose:
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = Console()

    english_class = literature.HighSchoolEnglishClass(
        None,
        milvus_uri,
        None,
        collection_name,
        console=sub_console,
    )

    console.print("Building chunk space")
    english_class.chunk_space.build()


@app.command(
    help="""
Ask a question about literature using the RAG pattern with the chunks prepared in the previous step.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
"""
)
def ask(loop: bool = False, question: str = None, verbose: bool = False):

    sub_console = None
    if verbose:
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = Console()

    english_class = literature.HighSchoolEnglishClass(
        milvus_uri,
        None,
        collection_name,
        console=sub_console,
    )

    while True:

        if question is None:
            q = Prompt.ask(
                literature.query_handler.user_prompt,
                default=literature.query_handler.default_question,
            )
        else:
            q = question

        for channel_id, answer in english_class.literature_expert.handle(None, None, q):
            console.print(Panel(answer, title="Assistant"))

        if loop:
            question = None
        else:
            break
