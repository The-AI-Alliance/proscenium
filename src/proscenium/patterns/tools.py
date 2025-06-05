from typing import Optional
from typing import Any
import logging
import json

from rich.console import Group
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Console

from aisuite import Client as AISuiteClient
from aisuite.framework.message import ChatCompletionMessageToolCall

from gofannon.base import BaseTool

from proscenium.history import messages_table

log = logging.getLogger(__name__)


def evaluate_tool_call(tool_map: dict, tool_call: ChatCompletionMessageToolCall) -> Any:

    function_name = tool_call.function.name
    # TODO validate the arguments?
    function_args = json.loads(tool_call.function.arguments)

    log.info(f"Evaluating tool call: {function_name} with args {function_args}")

    function_response = tool_map[function_name](**function_args)

    log.info(f"   Response: {function_response}")

    return function_response


def tool_response_message(
    tool_call: ChatCompletionMessageToolCall, tool_result: Any
) -> dict:

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_call.function.name,
        "content": json.dumps(tool_result),
    }


def evaluate_tool_calls(tool_call_message, tool_map: dict) -> list[dict]:

    tool_call: ChatCompletionMessageToolCall

    log.info("Evaluating tool calls")

    new_messages: list[dict] = []

    for tool_call in tool_call_message.tool_calls:
        function_response = evaluate_tool_call(tool_map, tool_call)
        new_messages.append(tool_response_message(tool_call, function_response))

    log.info("Tool calls evaluated")

    return new_messages


def complete_for_tool_applications(
    chat_completion_client: AISuiteClient,
    model_id: str,
    messages: list,
    tool_desc_list: list,
    temperature: float,
    console: Optional[Console] = None,
):

    if console is not None:
        panel = complete_with_tools_panel(
            "complete for tool applications",
            model_id,
            tool_desc_list,
            messages,
            temperature,
        )
        console.print(panel)

    response = chat_completion_client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=temperature,
        tools=tool_desc_list,  # tool_choice="auto",
    )

    return response


def complete_with_tool_results(
    chat_completion_client: AISuiteClient,
    model_id: str,
    messages: list,
    tool_call_message: dict,
    tool_evaluation_messages: list[dict],
    tool_desc_list: list,
    temperature: float,
    console: Optional[Console] = None,
):

    messages.append(tool_call_message)
    messages.extend(tool_evaluation_messages)

    if console is not None:
        panel = complete_with_tools_panel(
            "complete call with tool results",
            model_id,
            tool_desc_list,
            messages,
            temperature,
        )
        console.print(panel)

    response = chat_completion_client.chat.completions.create(
        model=model_id,
        messages=messages,
    )

    return response.choices[0].message.content


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
