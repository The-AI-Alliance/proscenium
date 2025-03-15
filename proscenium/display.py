
from typing import List

from rich import print
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.console import Group

from pymilvus import MilvusClient

def header() -> Text:
    text = Text()
    text.append("Proscenium 🎭\n", style="bold")
    text.append("The AI Alliance\n", style="bold")
    # TODO version, timestamp, ...
    return text

def chunk_hits_table(
    chunks: list[dict]
) -> Table:

    table = Table(title="Closest Chunks", show_lines=True)
    table.add_column("id", justify="right", style="cyan")
    table.add_column("distance", style="magenta")
    table.add_column("entity.text", justify="right", style="green")
    for chunk in chunks:
        table.add_row(str(chunk['id']), str(chunk['distance']), chunk['entity']['text'])
    return table

def triples_table(
    triples: List[tuple[str, str, str]],
    title: str) -> Table:

    table = Table(title=title, show_lines=False)
    table.add_column("Subject", justify="left", style="blue")
    table.add_column("Predicate", justify="left", style="green")
    table.add_column("Object", justify="left", style="red")
    for triple in triples:
        table.add_row(*triple)

    return table

def pairs_table(
    subject_predicate_pairs: List[tuple[str, str]],
    title: str) -> Table:

    table = Table(title=title, show_lines=False)
    table.add_column("Subject", justify="left", style="blue")
    table.add_column("Predicate", justify="left", style="green")
    for pair in subject_predicate_pairs:
        table.add_row(*pair)

    return table

def collection_panel(
    client: MilvusClient,
    collection_name: str) -> Panel:

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

    return panel

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
        function_descriptions_panel(tool_desc_list),
        messages_table(messages)), title=title)

    return panel

def parameters_table(parameters: list[dict]) -> Table:

    table = Table(title="Parameters", show_lines=False, box=None)
    table.add_column("name", justify="right")
    table.add_column("type", justify="left")
    table.add_column("description", justify="left")

    for name, props in parameters['properties'].items():
        table.add_row(name, props['type'], props['description'])    

    # TODO denote required params

    return table

def function_description_panel(fd: dict) -> Panel:

    fn = fd['function']

    text = Text(f"{fd['type']} {fn['name']}: {fn['description']}\n")

    pt = parameters_table(fn['parameters'])

    panel = Panel(Group(text, pt))

    return panel

def function_descriptions_panel(function_descriptions: list[dict]) -> Panel:

    sub_panels = [function_description_panel(fd) for fd in function_descriptions]

    panel = Panel(Group(*sub_panels), title="Function Descriptions")

    return panel
