from typing import List

from rich import print
from rich.panel import Panel
from rich.text import Text
from thespian.actors import Actor

from gofannon.base import BaseTool

from proscenium.verbs.complete import (
    complete_for_tool_applications,
    evaluate_tool_calls,
    complete_with_tool_results,
)
from proscenium.verbs.invoke import process_tools


def tool_applier_actor_class(
    tools: List[BaseTool],
    system_message: str,
    model_id: str,
    temperature: float = 0.75,
    rich_output: bool = False,
):

    tool_map, tool_desc_list = process_tools(tools)

    class ToolApplier(Actor):

        def receiveMessage(self, message, sender):

            response = apply_tools(
                model_id=model_id,
                system_message=system_message,
                message=message,
                tool_desc_list=tool_desc_list,
                tool_map=tool_map,
                temperature=temperature,
                rich_output=rich_output,
            )

            self.send(sender, response)

    return ToolApplier


def apply_tools(
    model_id: str,
    system_message: str,
    message: str,
    tool_desc_list: list,
    tool_map: dict,
    temperature: float = 0.75,
    rich_output: bool = False,
) -> str:

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message},
    ]

    response = complete_for_tool_applications(
        model_id, messages, tool_desc_list, temperature, rich_output
    )

    tool_call_message = response.choices[0].message

    if tool_call_message.tool_calls is None or len(tool_call_message.tool_calls) == 0:

        if rich_output:
            print(
                Panel(
                    Text(str(tool_call_message.content)),
                    title="Tool Application Response",
                )
            )

        print("No tool applications detected")

        return tool_call_message.content

    else:

        if rich_output:
            print(
                Panel(Text(str(tool_call_message)), title="Tool Application Response")
            )

        tool_evaluation_messages = evaluate_tool_calls(
            tool_call_message, tool_map, rich_output
        )

        result = complete_with_tool_results(
            model_id,
            messages,
            tool_call_message,
            tool_evaluation_messages,
            tool_desc_list,
            temperature,
            rich_output,
        )

        return result
