from rich.console import Group
from rich.table import Table
from rich.text import Text
from rich.panel import Panel

from .chat import messages_table


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
