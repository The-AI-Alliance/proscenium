import logging
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import typer

from demo.settings import abacus

app = typer.Typer(help="""Arithmetic question answering.""")

console = Console()

log = logging.getLogger(__name__)


@app.command(help="Ask a natural langauge arithmetic question.")
def ask(verbose: bool = False):

    if verbose:
        log.setLevel(logging.INFO)
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)

    character = abacus.Abacus(None)

    question = Prompt.ask(
        "What is your arithmetic question?",
        default="What is 33312-457? And what is 3+3?",
    )

    for channel_id, message in character.handle(None, None, question):
        console.print(Panel(message, title="Answer"))
