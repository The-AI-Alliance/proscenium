from typing import Optional
import logging

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from proscenium.verbs.complete import (
    complete_for_tool_applications,
    evaluate_tool_calls,
    complete_with_tool_results,
)

log = logging.getLogger(__name__)


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
