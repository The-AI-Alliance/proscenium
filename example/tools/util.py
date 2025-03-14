
from typing import List

from aisuite import Client
from thespian.actors import Actor

from gofannon.base import BaseTool

from proscenium.complete import apply_tools
from proscenium.invoke import process_tools

def tool_applier_actor_class(
    tools: List[BaseTool],
    system_message: str,
    model_id: str
):

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

    return ToolApplier
