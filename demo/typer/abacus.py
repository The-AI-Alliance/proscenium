from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
import typer
from thespian.actors import ActorSystem

from demo.config import default_model_id

from proscenium.scripts.tools import apply_tools, tool_applier_actor_class

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


@app.command(
    help="Ask a natural langauge arithmetic question. (Implemented with actors.)"
)
def ask_actor():

    abacus_actor_class = tool_applier_actor_class(
        tools=domain.tools,
        system_message=domain.system_message,
        model_id=model_id,
        rich_output=True,
    )

    tool_applier = ActorSystem().createActor(abacus_actor_class)

    question = "What is 33312-457? And what is 3+3?"

    answer = ActorSystem().ask(tool_applier, question, 1)

    print(Panel(answer, title="Answer"))
