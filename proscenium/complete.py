
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

#from proscenium.display import console

client = Client()

def complete_simple(
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    rich_output: bool = False) -> str:

    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    temperature = 0.75

    if rich_output:
        messages_table = Table(title="Messages", show_lines=True)
        messages_table.add_column("Role", justify="left", style="blue")
        messages_table.add_column("Content", justify="left", style="green")
        for message in messages:
            messages_table.add_row(message["role"], message["content"])

        params_text = Text(f"""
    model_id: {model_id}
    temperature: {temperature}
    """)

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

def evaluate_tool_call(tool_map: dict, tool_call: ChatCompletionMessageToolCall) -> Any:
    function_name = tool_call.function.name
    # TODO validate the arguments?
    function_args = json.loads(tool_call.function.arguments)
    function_response = tool_map[function_name](**function_args)
    return function_response

def tool_response_message(tool_call: ChatCompletionMessageToolCall, tool_result: Any) -> dict:
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": tool_call.function.name,
        "content": json.dumps(tool_result)
    }

def evaluate_tool_calls(tool_call_message, tool_map: dict) -> list[dict]:
    tool_call: ChatCompletionMessageToolCall

    new_messages: list[dict] = []

    for tool_call in tool_call_message.tool_calls:
        function_response = evaluate_tool_call(tool_map, tool_call)
        new_messages.append(tool_response_message(tool_call, function_response))

    return new_messages


def apply_tools(
    system_message: str,
    message: str,
    tool_desc_list: list,
    tool_map: dict,
    client: Client,
    model: str):

    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": message},
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.75,
        tools=tool_desc_list, # tool_choice="auto",
    )
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tool_desc_list, # tool_choice="auto",
    )

    tool_call_message = response.choices[0].message

    if tool_call_message.tool_calls is None:
        return tool_call_message.content
    else:
        messages.append(tool_call_message)
        tool_evaluation_messages = evaluate_tool_calls(tool_call_message, tool_map)

        messages.extend(tool_evaluation_messages)

        second_response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_desc_list
        )

        return second_response.choices[0].message.content
