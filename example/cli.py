import typer

import logging
from rich import print
from proscenium.display import header

from example.rag.typer_app import app as rag_app
from example.graph_rag.typer_app import app as graph_rag_app
from example.tools.typer_app import app as tools_app

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

app = typer.Typer()

app.add_typer(rag_app, name="rag")
app.add_typer(graph_rag_app, name="graph-rag")
app.add_typer(tools_app, name="tools")

if __name__ == "__main__":
    print(header())
    app()
