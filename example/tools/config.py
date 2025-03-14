
from thespian.actors import Actor
from aisuite import Client

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.complete import apply_tools
from proscenium.invoke import process_tools

tools = [Addition, Subtraction, Multiplication, Division]

system_message = "Perform any referenced arithmetic."

#model_id = "ollama:llama3.2"
model_id = "openai:gpt-4o"


question = "What is 33312-457? And what is 3+3?"
# question = "What is your favorite color?"
