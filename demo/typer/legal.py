import os
from pathlib import Path
import typer
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt

from proscenium.verbs.know import knowledge_graph_client

from proscenium.scripts.document_enricher import enrich_documents
from proscenium.scripts.knowledge_graph import load_knowledge_graph
from proscenium.scripts.entity_resolver import load_entity_resolver
from proscenium.scripts.graph_rag import answer_question

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
    verbose: bool = False,
):

    enrich_documents(
        domain.retriever(docs_per_dataset),
        domain.doc_as_rich,
        output,
        domain.default_chunk_extraction_model_id,
        domain.chunk_extraction_template,
        domain.LegalOpinionChunkExtractions,
        domain.doc_enrichments,
        delay=0.1,
        verbose=verbose,
    )


@app.command(
    help=f"""Load enrichments from a .jsonl file into the knowledge graph.
{neo4j_help}"""
)
def load_graph(
    input: Path = default_enrichment_jsonl_file,
):
    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    load_knowledge_graph(
        driver,
        input,
        domain.LegalOpinionEnrichments,
        domain.doc_enrichments_to_graph,
    )

    driver.close()


@app.command(
    help=f"""Show the knowledge graph as stored in the graph db.
{neo4j_help}"""
)
def show_graph():

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    domain.show_knowledge_graph(driver)

    driver.close()


@app.command(
    help=f"""Load the vector db used for field disambiguation.
Writes to milvus at MILVUS_URI, with a default of {default_milvus_uri}.
{neo4j_help}"""
)
def load_resolver():

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
    neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
    neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    load_entity_resolver(
        driver,
        domain.resolvers,
        milvus_uri,
    )

    driver.close()


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

    while True:

        if question is None:
            q = Prompt.ask(
                domain.user_prompt,
                default=domain.default_question,
            )
        else:
            q = question

        answer = answer_question(
            q,
            domain.default_query_extraction_model_id,
            milvus_uri,
            driver,
            domain.default_generation_model_id,
            domain.query_extract,
            domain.extract_to_context,
            domain.context_to_prompts,
            verbose,
        )

        if answer:
            print(Panel(answer, title="Answer"))
        else:
            print("No answer")

        if loop:
            question = None
        else:
            break

    driver.close()
