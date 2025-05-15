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

from typing import Optional
from typing import Any
import logging
import json

from rich.console import Console
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aisuite import Client
from aisuite.framework.message import ChatCompletionMessageToolCall

from proscenium.verbs.display.tools import complete_with_tools_panel

log = logging.getLogger(__name__)

provider_configs = {
    # TODO expose this
    "ollama": {"timeout": 180},
}

client = Client(provider_configs=provider_configs)


def complete_simple(
    model_id: str, system_prompt: str, user_prompt: str, **kwargs
) -> str:

    console = kwargs.pop("console", None)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    if console is not None:

        kwargs_text = "\n".join([str(k) + ": " + str(v) for k, v in kwargs.items()])

        params_text = Text(
            f"""
model_id: {model_id}
{kwargs_text}
    """
        )

        messages_table = Table(title="Messages", show_lines=True)
        messages_table.add_column("Role", justify="left")
        messages_table.add_column("Content", justify="left")  # style="green"
        for message in messages:
            messages_table.add_row(message["role"], message["content"])

        call_panel = Panel(
            Group(params_text, messages_table), title="complete_simple call"
        )
        console.print(call_panel)

    response = client.chat.completions.create(
        model=model_id, messages=messages, **kwargs
    )
    response = response.choices[0].message.content

    if console is not None:
        console.print(Panel(response, title="Response"))

    return response


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

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=temperature,
        tools=tool_desc_list,  # tool_choice="auto",
    )

    return response


def complete_with_tool_results(
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

    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
    )

    return response.choices[0].message.content
