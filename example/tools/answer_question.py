from rich import print
from proscenium.display import print_header

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from aisuite import Client

from proscenium.complete import apply_tools
from proscenium.invoke import process_tools

tools = [Addition, Subtraction, Multiplication, Division]

tool_map, tool_desc_list = process_tools(tools)

client = Client()

print_header()

answer = apply_tools(
    system_message = "Perform any referenced arithmetic.",
    message = "What is 33312-457? And what is 3+3?",
    # message = "What is your favorite color?",
    tool_desc_list = tool_desc_list,
    tool_map = tool_map,
    client = client,
    #model = "ollama:llama3.2"
    model = "openai:gpt-4o"
)

print(answer)
