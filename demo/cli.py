import typer

import logging
from rich import print
from proscenium.verbs.display import header

from demo.typer.abacus import app as abacus_app
from demo.typer.literature import app as literature_app
from demo.typer.legal import app as legal_app

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

app = typer.Typer()

app.add_typer(literature_app, name="literature")
app.add_typer(legal_app, name="legal")
app.add_typer(abacus_app, name="abacus")

if __name__ == "__main__":
    print(header())
    app()
