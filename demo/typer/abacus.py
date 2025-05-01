import logging
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
import typer

import demo.domains.abacus as domain

app = typer.Typer(help="""Arithmetic question answering.""")

console = Console()


@app.command(help="Ask a natural langauge arithmetic question.")
def ask(verbose: bool = False):

    sub_console = None
    if verbose:
        logging.basicConfig(level=logging.INFO)
        sub_console = Console()

    handle = domain.make_handler(console=sub_console)

    question = Prompt.ask(
        "What is your arithmetic question?",
        default="What is 33312-457? And what is 3+3?",
    )

    for message in handle(question):
        console.print(Panel(message, title="Answer"))
