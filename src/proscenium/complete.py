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

import logging

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from aisuite import Client as AISuiteClient

log = logging.getLogger(__name__)


def complete_simple(
    chat_completion_client: AISuiteClient,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    **kwargs,
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

    response = chat_completion_client.chat.completions.create(
        model=model_id, messages=messages, **kwargs
    )
    response = response.choices[0].message.content

    if console is not None:
        console.print(Panel(response, title="Response"))

    return response
