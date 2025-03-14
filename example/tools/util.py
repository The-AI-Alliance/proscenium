
from typing import List

from aisuite import Client
from thespian.actors import Actor

from gofannon.base import BaseTool

from proscenium.complete import apply_tools
from proscenium.invoke import process_tools

def tool_applier_actor_class(
    tools: List[BaseTool],
    system_message: str,
    model_id: str,
    temperature: float = 0.75,
    rich_output: bool = False):

    tool_map, tool_desc_list = process_tools(tools)

    class ToolApplier(Actor):

        def receiveMessage(self, message, sender):

            response = apply_tools(
                model_id = model_id,
                system_message = system_message,
                message = message,
                tool_desc_list = tool_desc_list,
                tool_map = tool_map,
                temperature = temperature,
                rich_output = rich_output)

            self.send(sender, response)

    return ToolApplier
