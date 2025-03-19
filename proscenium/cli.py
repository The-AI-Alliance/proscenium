import typer

import logging
from rich import print
from proscenium.verbs.display import header

from proscenium.typer.abacus import app as abacus_app
from proscenium.typer.rag import app as rag_app
from proscenium.typer.graph_rag import app as graph_rag_app

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

app = typer.Typer()

app.add_typer(rag_app, name="rag")
app.add_typer(graph_rag_app, name="graph-rag")
app.add_typer(abacus_app, name="abacus")

if __name__ == "__main__":
    print(header())
    app()
