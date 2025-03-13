
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

    print("Collection row count:", client.get_collection_stats(collection_name)['row_count'])
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
            str(field['type']),                # Milvus DataType
            "\n".join([f"{k}: {v}" for k, v in field['params'].items()]),
            str(field.get('auto_id', "-")),    # bool
            str(field.get('is_primary', "-"))) # bool

    panel = Panel(Group(params_text, fields_table), title=f"Collection {collection_name}")

    print(panel)
