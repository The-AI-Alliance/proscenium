from rich import print
from rich.panel import Panel
from rich.prompt import Prompt

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.display import header
from proscenium.invoke import process_tools

import example.tools.util as util

tools = [Addition, Subtraction, Multiplication, Division]

tool_map, tool_desc_list = process_tools(tools)

print(header())

# "What is your favorite color?"

question = Prompt.ask(
    f"What is your arithmetic question?",
    default = "What is 33312-457? And what is 3+3?"
    )

answer = util.apply_tools(
    model_id = "ollama:llama3.2",
    # model_id = "ollama:granite3.2",
    # model_id = "openai:gpt-4o",
    system_message = "Perform any referenced arithmetic.",
    message = question,
    tool_desc_list = tool_desc_list,
    tool_map = tool_map,
    rich_output = True
)

print(Panel(answer, title="Answer"))
