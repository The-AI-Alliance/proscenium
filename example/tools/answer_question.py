from rich import print
from thespian.actors import ActorSystem
from proscenium.display import print_header

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

import example.tools.util as util

tools = [Addition, Subtraction, Multiplication, Division]

system_message = "Perform any referenced arithmetic."

#model_id = "ollama:llama3.2"
model_id = "openai:gpt-4o"

applier_class = util.tool_applier_actor_class(
    tools=tools,
    system_message=system_message,
    model_id=model_id
)

tool_applier = ActorSystem().createActor(applier_class)

print_header()

question = "What is 33312-457? And what is 3+3?"
# question = "What is your favorite color?"

answer = ActorSystem().ask(tool_applier, question, 1)

print(answer)
