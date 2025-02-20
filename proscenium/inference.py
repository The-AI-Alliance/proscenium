
from typing import Any
import json
from aisuite import Client
from aisuite.framework.message import ChatCompletionMessageToolCall

client = Client()

def complete_simple(model_id: str, system_prompt: str, user_prompt: str) -> str:
    response = client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.75,
    )
    return response.choices[0].message.content

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
