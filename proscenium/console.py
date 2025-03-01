
from rich import print
from rich.table import Table

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
