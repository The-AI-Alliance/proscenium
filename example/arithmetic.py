

from thespian.actors import Actor

from aisuite import Client
from proscenium.inference import apply_tools

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division
from proscenium.functions import process_tools

class Abacus(Actor):

    client = Client()

    tool_map, tool_desc_list = process_tools([Addition, Subtraction, Multiplication, Division])

    system_message = "Perform any referenced arithmetic."

    model = "openai:gpt-4o" # os.environ["OPENAI_API_KEY"]
    # model = "anthropic:claude-3-5-sonnet-20240620" # os.environ["ANTHROPIC_API_KEY"]

    def receiveMessage(self, message, sender):

        response = apply_tools(
            system_message=self.system_message,
            message=message,
            tool_desc_list=self.tool_desc_list,
            tool_map=self.tool_map,
            client=self.client,
            model=self.model
        )

        self.send(sender, response)
