from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.console import Group
from pymilvus import MilvusClient


def chunk_hits_table(chunks: list[dict]) -> Table:

    table = Table(title="Closest Chunks", show_lines=True)
    table.add_column("id", justify="right")
    table.add_column("distance")
    table.add_column("entity.text", justify="right")
    for chunk in chunks:
        table.add_row(str(chunk["id"]), str(chunk["distance"]), chunk["entity"]["text"])
    return table


def collection_panel(client: MilvusClient, collection_name: str) -> Panel:

    stats = client.get_collection_stats(collection_name)
    desc = client.describe_collection(collection_name)

    params_text = Text(
        f"""
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
    Enable Dynamic Field: {desc['enable_dynamic_field']}"""
    )

    params_panel = Panel(params_text, title="Params")

    fields_table = Table(title="Fields", show_lines=True)
    fields_table.add_column("id", justify="left")
    fields_table.add_column("name", justify="left")
    fields_table.add_column("description", justify="left")
    fields_table.add_column("type", justify="left")
    fields_table.add_column("params", justify="left")
    fields_table.add_column("auto_id", justify="left")
    fields_table.add_column("is_primary", justify="left")
    for field in desc["fields"]:
        fields_table.add_row(
            str(field["field_id"]),  # int
            field["name"],
            field["description"],
            field["type"].name,  # Milvus DataType
            "\n".join([f"{k}: {v}" for k, v in field["params"].items()]),
            str(field.get("auto_id", "-")),  # bool
            str(field.get("is_primary", "-")),
        )  # bool

    stats_text = Text("\n".join([f"{k}: {v}" for k, v in stats.items()]))
    stats_panel = Panel(stats_text, title="Stats")

    panel = Panel(
        Group(params_panel, fields_table, stats_panel),
        title=f"Collection {collection_name}",
    )

    return panel
