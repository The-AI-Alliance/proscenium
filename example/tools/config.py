
from thespian.actors import Actor
from aisuite import Client

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.complete import apply_tools
from proscenium.invoke import process_tools

model_id = "ollama:llama3.2"

system_message = "Perform any referenced arithmetic."

tools = [Addition, Subtraction, Multiplication, Division]

class ToolApplier(Actor):

    client = Client()

    tool_map, tool_desc_list = process_tools(tools)

    def receiveMessage(self, message, sender):

        response = apply_tools(
            system_message=system_message,
            message=message,
            tool_desc_list=self.tool_desc_list,
            tool_map=self.tool_map,
            client=self.client,
            model=model_id
        )

        self.send(sender, response)


question = "What is 33312-457? And what is 3+3?"
# question = "What is your favorite color?"
