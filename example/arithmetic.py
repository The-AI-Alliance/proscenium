

from thespian.actors import Actor
from aisuite import Client

from proscenium.invoke import apply_tools
from proscenium.invoke import process_tools

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

class Abacus(Actor):

    client = Client()

    tool_map, tool_desc_list = process_tools([Addition, Subtraction, Multiplication, Division])

    system_message = "Perform any referenced arithmetic."

    model = "ollama:llama3.2"

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

if __name__ == '__main__':
    from thespian.actors import ActorSystem
    from example.arithmetic import Abacus

    abacus = ActorSystem().createActor(Abacus)

    message = "What is 33312-457? And what is 3+3?"
    # message = "What is your favorite color?"

    answer = ActorSystem().ask(abacus, message, 1)
    print(answer)
