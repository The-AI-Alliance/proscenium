from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
import typer

from demo.config import default_model_id

from proscenium.scripts.tools import apply_tools

model_id = default_model_id

import demo.domains.abacus as domain

app = typer.Typer(help="""Arithmetic question answering.""")


@app.command(help="Ask a natural langauge arithmetic question.")
def ask():

    question = Prompt.ask(
        f"What is your arithmetic question?",
        default="What is 33312-457? And what is 3+3?",
    )

    answer = apply_tools(
        model_id=model_id,
        system_message=domain.system_message,
        message=question,
        tool_desc_list=domain.tool_desc_list,
        tool_map=domain.tool_map,
        rich_output=True,
    )

    print(Panel(answer, title="Answer"))
