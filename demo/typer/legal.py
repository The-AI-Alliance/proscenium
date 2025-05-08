import typer
import os
import logging
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from neo4j import GraphDatabase

from demo.scenes import legal

from demo.scenes.legal.doc_enrichments import DocumentEnrichments
from demo.scenes.legal.kg import CaseLawKnowledgeGraph, display_knowledge_graph
from demo.scenes.legal.entity_resolvers import (
    EntityResolvers,
    default_embedding_model_id,
)


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

console = Console()

log = logging.getLogger(__name__)


@app.command(help=f"Enrich documents from {', '.join(legal.docs.hf_dataset_ids)}.")
def enrich(
    docs_per_dataset: int = legal.docs.default_docs_per_dataset,
    output: Path = default_enrichment_jsonl_file,
    delay: float = legal.doc_enrichments.default_delay,
    verbose: bool = False,
):
    sub_console = None
    if verbose:
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = Console()

    doc_enrichments = DocumentEnrichments(docs_per_dataset, output, delay, sub_console)

    console.print("Enriching documents")
    doc_enrichments.build()


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

    sub_console = None
    if verbose:
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = Console()

    case_law_knowledge_graph = CaseLawKnowledgeGraph(
        input,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        console=sub_console,
    )

    console.print("Loading knowledge graph")
    case_law_knowledge_graph.build()


@app.command(
    help=f"""Display the knowledge graph as stored in the graph db.
{neo4j_help}"""
)
def display_graph(verbose: bool = False):

    if verbose:
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

    console.print("Showing knowledge graph")
    display_knowledge_graph(driver, console)


@app.command(
    help=f"""Load the vector db used for field disambiguation.
Writes to milvus at MILVUS_URI, with a default of {default_milvus_uri}.
{neo4j_help}"""
)
def load_resolver(verbose: bool = False):

    sub_console = None
    if verbose:
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)
        sub_console = Console()

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    entity_resolvers = EntityResolvers(
        milvus_uri,
        default_embedding_model_id,
        neo4j_uri,
        neo4j_username,
        neo4j_password,
        console=sub_console,
    )

    console.print("Loading entity resolver")
    entity_resolvers.build()


@app.command(
    help=f"""Ask a legal question using the knowledge graph and entity resolver established in the previous steps.
Uses milvus at MILVUS_URI, with a default of {default_milvus_uri}.
{neo4j_help}"""
)
def ask(loop: bool = False, question: str = None, verbose: bool = False):

    if verbose:
        logging.getLogger("proscenium").setLevel(logging.INFO)
        logging.getLogger("demo").setLevel(logging.INFO)

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

    law_librarian = legal.query_handler.LawLibrarian(driver, milvus_uri, None)

    while True:

        if question is None:
            q = Prompt.ask(
                legal.query_handler.user_prompt,
                default=legal.query_handler.default_question,
            )
        else:
            q = question

        console.print(Panel(q, title="Question"))

        for channel_id, answer in law_librarian.handle(None, None, q):
            console.print(Panel(answer, title="Answer"))

        if loop:
            question = None
        else:
            break

    driver.close()
