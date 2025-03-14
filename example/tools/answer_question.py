from rich import print
from rich.panel import Panel

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.display import header
from proscenium.complete import apply_tools
from proscenium.invoke import process_tools

tools = [Addition, Subtraction, Multiplication, Division]

tool_map, tool_desc_list = process_tools(tools)

print(header())

answer = apply_tools(
    model_id = "ollama:llama3.2",
    # model_id = "openai:gpt-4o",
    system_message = "Perform any referenced arithmetic.",
    message = "What is 33312-457? And what is 3+3?",
    # message = "What is your favorite color?",
    tool_desc_list = tool_desc_list,
    tool_map = tool_map,
    rich_output = True
)

print(Panel(answer, title="Answer"))
