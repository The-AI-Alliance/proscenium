
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
import typer
from thespian.actors import ActorSystem

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.typer.config import default_model_id
from proscenium.verbs.invoke import process_tools
from proscenium.scripts.tools import apply_tools, tool_applier_actor_class

model_id = default_model_id

app = typer.Typer()

@app.command()
def ask():

    tools = [Addition, Subtraction, Multiplication, Division]

    tool_map, tool_desc_list = process_tools(tools)

    # try "What is your favorite color?"
    question = Prompt.ask(
        f"What is your arithmetic question?",
        default = "What is 33312-457? And what is 3+3?"
    )

    answer = apply_tools(
        model_id = model_id,
        system_message = "Perform any referenced arithmetic.",
        message = question,
        tool_desc_list = tool_desc_list,
        tool_map = tool_map,
        rich_output = True
    )

    print(Panel(answer, title="Answer"))


@app.command()
def ask_actor():

    abacus_actor_class = tool_applier_actor_class(
        tools = [Addition, Subtraction, Multiplication, Division],
        system_message = "Perform any referenced arithmetic.",
        model_id = model_id,
        rich_output = True
    )

    tool_applier = ActorSystem().createActor(abacus_actor_class)

    question = "What is 33312-457? And what is 3+3?"
    # question = "What is your favorite color?"

    answer = ActorSystem().ask(tool_applier, question, 1)

    print(Panel(answer, title="Answer"))
