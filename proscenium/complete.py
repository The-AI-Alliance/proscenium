
"""
This module uses the [`aisuite`](https://github.com/andrewyng/aisuite) library
to interact with various LLM inference providers.

It provides functions to complete a simple chat prompt, evaluate a tool call,
and apply a list of tool calls to a chat prompt.

Providers tested with Proscenium include:

# AWS

Environment: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

Valid model ids:
- `aws:meta.llama3-1-8b-instruct-v1:0`

# Anthropic

Environment: `ANTHROPIC_API_KEY`

Valid model ids:
- `anthropic:claude-3-5-sonnet-20240620`

# OpenAI

Environment: `OPENAI_API_KEY`

Valid model ids:
- `openai:gpt-4o`

# Ollama

Command line, eg `ollama run llama3.2 --keepalive 2h`

Valid model ids:
- `ollama:llama3.2`
- `ollama:granite3.1-dense:2b`
"""

from typing import Any

import json
from rich import print
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aisuite import Client
from aisuite.framework.message import ChatCompletionMessageToolCall

from proscenium.display import complete_with_tools_panel

provider_configs = {
    # TODO expose this
    "ollama": {"timeout": 180},
}

client = Client(provider_configs=provider_configs)

def complete_simple(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.75,
    rich_output: bool = False) -> str:

    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if rich_output:

        params_text = Text(f"""
    model_id: {model_id}
    temperature: {temperature}
    """)

        messages_table = Table(title="Messages", show_lines=True)
        messages_table.add_column("Role", justify="left", style="blue")
        messages_table.add_column("Content", justify="left", style="green")
        for message in messages:
            messages_table.add_row(message["role"], message["content"])

        call_panel = Panel(Group(params_text, messages_table), title="complete_simple call")
        print(call_panel)

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=temperature,
    )
    response = response.choices[0].message.content

    if rich_output:
        print(Panel(response, title="Response"))

    return response

def evaluate_tool_call(
    tool_map: dict,
    tool_call: ChatCompletionMessageToolCall,
    rich_output: bool = False) -> Any:

    function_name = tool_call.function.name
    # TODO validate the arguments?
    function_args = json.loads(tool_call.function.arguments)

    if rich_output:
        print(f"Evaluating tool call: {function_name} with args {function_args}")

    function_response = tool_map[function_name](**function_args)

    if rich_output:
        print(f"   Response: {function_response}")

    return function_response

def tool_response_message(
        tool_call: ChatCompletionMessageToolCall,
        tool_result: Any) -> dict:

    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_call.function.name,
        "content": json.dumps(tool_result)
    }

def evaluate_tool_calls(
    tool_call_message,
    tool_map: dict,
    rich_output: bool = False) -> list[dict]:

    tool_call: ChatCompletionMessageToolCall

    if rich_output:
        print("Evaluating tool calls")

    new_messages: list[dict] = []

    for tool_call in tool_call_message.tool_calls:
        function_response = evaluate_tool_call(tool_map, tool_call, rich_output)
        new_messages.append(tool_response_message(tool_call, function_response))

    if rich_output:
        print("Tool calls evaluated")

    return new_messages


def complete_for_tool_applications(
    model_id: str,
    messages: list,
    tool_desc_list: list,
    temperature: float,
    rich_output: bool = False):

    if rich_output:
        panel = complete_with_tools_panel(
            "complete for tool applications",
            model_id, tool_desc_list, messages, temperature)
        print(panel)

    response = client.chat.completions.create(
        model = model_id,
        messages = messages,
        temperature = temperature,
        tools = tool_desc_list, # tool_choice="auto",
    )

    return response


def complete_with_tool_results(
    model_id: str,
    messages: list,
    tool_call_message: dict,
    tool_evaluation_messages: list[dict],
    tool_desc_list: list,
    temperature: float,
    rich_output: bool = False):

    messages.append(tool_call_message)
    messages.extend(tool_evaluation_messages)

    if rich_output:
        panel = complete_with_tools_panel(
            "complete call with tool results",
            model_id, tool_desc_list, messages, temperature)
        print(panel)

    response = client.chat.completions.create(
        model = model_id,
        messages = messages,
        tools = tool_desc_list
    )

    return response.choices[0].message.content

def apply_tools(
    model_id: str,
    system_message: str,
    message: str,
    tool_desc_list: list,
    tool_map: dict,
    temperature: float = 0.75,
    rich_output: bool = False
    ) -> str:

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message},
    ]

    response = complete_for_tool_applications(
        model_id,
        messages,
        tool_desc_list,
        temperature,
        rich_output
    )

    tool_call_message = response.choices[0].message

    if tool_call_message.tool_calls is None:

        if rich_output:
            print(Panel(Text(str(tool_call_message.content)), title="Tool Application Response"))

        print("No tool applications detected")

        return tool_call_message.content

    else:

        if rich_output:
            print(Panel(Text(str(tool_call_message)), title="Tool Application Response"))

        tool_evaluation_messages = evaluate_tool_calls(
            tool_call_message, tool_map, rich_output)

        result = complete_with_tool_results(
            model_id,
            messages,
            tool_call_message,
            tool_evaluation_messages,
            tool_desc_list,
            temperature,
            rich_output
        )

        return result

    