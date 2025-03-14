

from thespian.actors import Actor
from aisuite import Client

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.complete import apply_tools
from proscenium.invoke import process_tools

import example.tools.config as config

class Abacus(Actor):

    client = Client()

    tool_map, tool_desc_list = process_tools([Addition, Subtraction, Multiplication, Division])

    def receiveMessage(self, message, sender):

        response = apply_tools(
            system_message=config.system_message,
            message=message,
            tool_desc_list=self.tool_desc_list,
            tool_map=self.tool_map,
            client=self.client,
            model=config.model_id
        )

        self.send(sender, response)

if __name__ == '__main__':
    from thespian.actors import ActorSystem
    from example.tools.arithmetic import Abacus

    abacus = ActorSystem().createActor(Abacus)

    answer = ActorSystem().ask(abacus, config.question, 1)
    print(answer)
