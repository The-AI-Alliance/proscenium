
from typing import List
from rich.table import Table

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
