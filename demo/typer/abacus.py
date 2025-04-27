from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
import typer

import demo.domains.abacus as domain

app = typer.Typer(help="""Arithmetic question answering.""")


@app.command(help="Ask a natural langauge arithmetic question.")
def ask():

    handler = domain.make_handler(verbose=True)

    question = Prompt.ask(
        f"What is your arithmetic question?",
        default="What is 33312-457? And what is 3+3?",
    )

    for message in handler(question):
        print(Panel(message, title="Answer"))
