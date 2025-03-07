
from typing import List

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
