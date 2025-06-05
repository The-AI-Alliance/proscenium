from typing import Optional
import logging

from rich.console import Group
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Console

from proscenium.history import messages_table

from gofannon.base import BaseTool

from proscenium.complete import (
    complete_for_tool_applications,
    evaluate_tool_calls,
    complete_with_tool_results,
)

log = logging.getLogger(__name__)


def process_tools(tools: list[BaseTool]) -> tuple[dict, list]:
    applied_tools = [F() for F in tools]
    tool_map = {f.name: f.fn for f in applied_tools}
    tool_desc_list = [f.definition for f in applied_tools]
    return tool_map, tool_desc_list


def parameters_table(parameters: list[dict]) -> Table:

    table = Table(title="Parameters", show_lines=False, box=None)
    table.add_column("name", justify="right")
    table.add_column("type", justify="left")
    table.add_column("description", justify="left")

    for name, props in parameters["properties"].items():
        table.add_row(name, props["type"], props["description"])

    # TODO denote required params

    return table


def function_description_panel(fd: dict) -> Panel:

    fn = fd["function"]

    text = Text(f"{fd['type']} {fn['name']}: {fn['description']}\n")

    pt = parameters_table(fn["parameters"])

    panel = Panel(Group(text, pt))

    return panel


def function_descriptions_panel(function_descriptions: list[dict]) -> Panel:

    sub_panels = [function_description_panel(fd) for fd in function_descriptions]

    panel = Panel(Group(*sub_panels), title="Function Descriptions")

    return panel


def complete_with_tools_panel(
    title: str, model_id: str, tool_desc_list: list, messages: list, temperature: float
) -> Panel:

    text = Text(
        f"""
model_id: {model_id}
temperature: {temperature}
"""
    )

    panel = Panel(
        Group(
            text, function_descriptions_panel(tool_desc_list), messages_table(messages)
        ),
        title=title,
    )

    return panel


def apply_tools(
    model_id: str,
    system_message: str,
    message: str,
    tool_desc_list: list,
    tool_map: dict,
    temperature: float = 0.75,
    console: Optional[Console] = None,
) -> str:

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message},
    ]

    response = complete_for_tool_applications(
        model_id, messages, tool_desc_list, temperature, console
    )

    tool_call_message = response.choices[0].message

    if tool_call_message.tool_calls is None or len(tool_call_message.tool_calls) == 0:

        if console is not None:
            console.print(
                Panel(
                    Text(str(tool_call_message.content)),
                    title="Tool Application Response",
                )
            )

        log.info("No tool applications detected")

        return tool_call_message.content

    else:

        if console is not None:
            console.print(
                Panel(Text(str(tool_call_message)), title="Tool Application Response")
            )

        tool_evaluation_messages = evaluate_tool_calls(tool_call_message, tool_map)

        result = complete_with_tool_results(
            model_id,
            messages,
            tool_call_message,
            tool_evaluation_messages,
            tool_desc_list,
            temperature,
            console,
        )

        return result
