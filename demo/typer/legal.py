import typer
from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
from pathlib import Path

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

neo4j_uri = "bolt://localhost:7687"  # os.environ["NEO4J_URI"]
neo4j_username = "neo4j"  # os.environ["NEO4J_USERNAME"]
neo4j_password = "password"  # os.environ["NEO4J_PASSWORD"]

default_milvus_uri = "file:/grag-milvus.db"


@app.command(
    help=f"Enrich documents from {', '.join(domain.hf_dataset_ids)} and write to {default_enrichment_jsonl_file}."
)
def enrich(docs_per_dataset: int = None, verbose: bool = False):

    enrich_documents(
        domain.retriever(docs_per_dataset),
        domain.doc_as_rich,
        default_enrichment_jsonl_file,
        domain.default_chunk_extraction_model_id,
        domain.chunk_extraction_template,
        domain.LegalOpinionChunkExtractions,
        domain.doc_enrichments,
        delay=0.1,
        verbose=verbose,
    )


@app.command(
    help=f"Load enrichments from {default_enrichment_jsonl_file} into the knowledge graph."
)
def load_graph():

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    load_knowledge_graph(
        driver,
        default_enrichment_jsonl_file,
        domain.LegalOpinionEnrichments,
        domain.doc_enrichments_to_graph,
    )

    driver.close()


@app.command(help="Show the knowledge graph as stored in the graph db.")
def show_graph():

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    domain.show_knowledge_graph(driver)

    driver.close()


@app.command(help="Load the vector db used for entity resolution.")
def load_resolver():

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    load_entity_resolver(
        driver,
        domain.resolvers,
        default_milvus_uri,
    )

    driver.close()


@app.command(
    help="Ask a legal question using the knowledge graph and entity resolver established in the previous steps."
)
def ask(loop: bool = False, verbose: bool = False):

    driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

    while True:
        question = Prompt.ask(
            domain.user_prompt,
            default=domain.default_question,
        )

        answer = answer_question(
            question,
            domain.default_query_extraction_model_id,
            default_milvus_uri,
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

        if not loop:
            break

    driver.close()
