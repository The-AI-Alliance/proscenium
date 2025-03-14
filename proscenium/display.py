
from typing import List

from rich import print
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Group
from pymilvus import MilvusClient

def print_header() -> None:
    print("[bold]Proscenium[/bold]", ":performing_arts:")
    print("[bold]The AI Alliance[/bold]")
    # TODO version, timestamp, ...
    print()

def display_chunk_hits(
    chunks: list[dict]
):
    table = Table(title="Closest Chunks", show_lines=True)
    table.add_column("id", justify="right", style="cyan")
    table.add_column("distance", style="magenta")
    table.add_column("entity.text", justify="right", style="green")
    for chunk in chunks:
        table.add_row(str(chunk['id']), str(chunk['distance']), chunk['entity']['text'])
    print(table)

def display_triples(triples: List[tuple[str, str, str]], title: str) -> None:
    table = Table(title=title, show_lines=False)
    table.add_column("Subject", justify="left", style="blue")
    table.add_column("Predicate", justify="left", style="green")
    table.add_column("Object", justify="left", style="red")
    for triple in triples:
        table.add_row(*triple)
    print(table)

def display_pairs(subject_predicate_pairs: List[tuple[str, str]], title: str) -> None:
    table = Table(title=title, show_lines=False)
    table.add_column("Subject", justify="left", style="blue")
    table.add_column("Predicate", justify="left", style="green")
    for pair in subject_predicate_pairs:
        table.add_row(*pair)
    print(table)

def display_collection(client: MilvusClient, collection_name: str) -> None:

    stats = client.get_collection_stats(collection_name)
    desc = client.describe_collection(collection_name)

    params_text = Text(f"""
    Collection Name: {desc['collection_name']}
    Auto ID: {desc['auto_id']}
    Num Shards: {desc['num_shards']}
    Description: {desc['description']}
    Functions: {desc['functions']}
    Aliases: {desc['aliases']}
    Collection ID: {desc['collection_id']}
    Consistency Level: {desc['consistency_level']}
    Properties: {desc['properties']}
    Num Partitions: {desc['num_partitions']}
    Enable Dynamic Field: {desc['enable_dynamic_field']}""")

    params_panel = Panel(params_text, title="Params")

    fields_table = Table(title="Fields", show_lines=True)
    fields_table.add_column("id", justify="left", style="blue")
    fields_table.add_column("name", justify="left", style="green")
    fields_table.add_column("description", justify="left", style="green")
    fields_table.add_column("type", justify="left", style="green")
    fields_table.add_column("params", justify="left", style="green")
    fields_table.add_column("auto_id", justify="left", style="green")
    fields_table.add_column("is_primary", justify="left", style="green")
    for field in desc['fields']:
        fields_table.add_row(
            str(field['field_id']),            # int
            field['name'],
            field['description'],
            field['type'].name,                # Milvus DataType
            "\n".join([f"{k}: {v}" for k, v in field['params'].items()]),
            str(field.get('auto_id', "-")),    # bool
            str(field.get('is_primary', "-"))) # bool

    stats_text = Text("\n".join([f"{k}: {v}" for k, v in stats.items()]))
    stats_panel = Panel(stats_text, title="Stats")

    panel = Panel(Group(
        params_panel,
        fields_table,
        stats_panel), title=f"Collection {collection_name}")

    print(panel)

def messages_table(messages: list) -> Table:

    table = Table(title="Messages in Chat Context", show_lines=True)
    table.add_column("Role", justify="left", style="blue")
    table.add_column("Content", justify="left", style="green")
    for message in messages:
        if type(message) is dict:
            role = message["role"]
            content = ""
            if role == 'tool':
                content = f"""tool call id = {message['tool_call_id']}
fn name = {message['name']}
result = [black]{message['content']}"""
            elif role == 'assistant':
                content = f"""{str(message)}"""
            else:
                content = message['content']
            table.add_row(role, content)
        else:
            role = message.role
            content = ""
            if role == 'tool':
                content = f"""tool call id = {message.tool_call_id}
fn name = {message.name}
result = [black]{message['content']}"""
            elif role == 'assistant':
                content = f"""{str(message)}"""
            else:
                content = message.content
            table.add_row(role, content)

    return table

def complete_with_tools_panel(
    title: str,
    model_id: str,
    tool_desc_list: list,
    messages: list,
    temperature: float) -> Panel:

    text = Text(f"""
model_id: {model_id}
temperature: {temperature}
""")

    panel = Panel(Group(
        text,
        function_descriptions_table(tool_desc_list),
        messages_table(messages)), title=title)

    return panel

def parameters_table(parameters: list[dict]) -> Table:
    table = Table(title="Parameters", show_lines=False)
    table.add_column("name", justify="left", style="blue")
    table.add_column("type", justify="left", style="green")
    table.add_column("description", justify="left", style="green")
    for name, props in parameters['properties'].items():
        table.add_row(name, props['type'], props['description'])    
    #"\n".join([f"{k}: {v}" for k, v in fn['parameters'].items()]
    return table

def function_descriptions_table(function_descriptions: list[dict]) -> Table:

    table = Table(title="Function Descriptions", show_lines=True)
    table.add_column("type", justify="left", style="blue")
    table.add_column("name", justify="left", style="blue")
    table.add_column("description", justify="left", style="green")
    table.add_column("parameters", justify="left", style="green")

    for fd in function_descriptions:
        fn = fd['function']
        table.add_row(
            fd['type'],
            fn['name'],
            fn['description'],
            parameters_table(fn['parameters'])
        )

    return table
