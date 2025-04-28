import os
from pathlib import Path
import typer
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt

from proscenium.verbs.know import knowledge_graph_client

import demo.domains.legal as domain

app = typer.Typer(
    help="""
Graph extraction and question answering with GraphRAG on caselaw.
"""
)

default_enrichment_jsonl_file = Path("enrichments.jsonl")

default_neo4j_uri = "bolt://localhost:7687"
default_neo4j_username = "neo4j"
default_neo4j_password = "password"

neo4j_help = f"""Uses Neo4j at NEO4J_URI, with a default of {default_neo4j_uri}, and
auth credentials NEO4J_USERNAME and NEO4J_PASSWORD, with defaults of
{default_neo4j_username} and {default_neo4j_password}."""

default_milvus_uri = "file:/grag-milvus.db"


@app.command(help=f"Enrich documents from {', '.join(domain.hf_dataset_ids)}.")
def enrich(
    docs_per_dataset: int = None,
    output: Path = default_enrichment_jsonl_file,
    delay: float = 0.1,
    verbose: bool = False,
):

    enrich = domain.make_document_enricher(docs_per_dataset, output, delay, verbose)

    print("Enriching documents")
    enrich()


@app.command(
    help=f"""Load enrichments from a .jsonl file into the knowledge graph.
{neo4j_help}"""
)
def load_graph(
    input: Path = default_enrichment_jsonl_file,
    verbose: bool = False,
):
    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    load = domain.make_kg_loader(
        input, neo4j_uri, neo4j_username, neo4j_password, verbose
    )

    print("Loading knowledge graph")
    load()


@app.command(
    help=f"""Show the knowledge graph as stored in the graph db.
{neo4j_help}"""
)
def show_graph():

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    show = domain.make_kg_shower(neo4j_uri, neo4j_username, neo4j_password)

    print("Showing knowledge graph")
    show()


@app.command(
    help=f"""Load the vector db used for field disambiguation.
Writes to milvus at MILVUS_URI, with a default of {default_milvus_uri}.
{neo4j_help}"""
)
def load_resolver(verbose: bool = False):

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    load = domain.make_entity_resolver_loader(
        milvus_uri, neo4j_uri, neo4j_username, neo4j_password, verbose
    )
    print("Loading entity resolver")
    load()


@app.command(
    help=f"""Ask a legal question using the knowledge graph and entity resolver established in the previous steps.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
{neo4j_help}"""
)
def ask(loop: bool = False, question: str = None, verbose: bool = False):

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    handle = domain.make_handler(driver, milvus_uri, verbose)

    while True:

        if question is None:
            q = Prompt.ask(
                domain.user_prompt,
                default=domain.default_question,
            )
        else:
            q = question

        print(Panel(q, title="Question"))

        for answer in handle(q):
            print(Panel(answer, title="Answer"))

        if loop:
            question = None
        else:
            break

    driver.close()
