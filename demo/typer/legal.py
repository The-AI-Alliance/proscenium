import typer
from rich import print
from rich.panel import Panel

from proscenium.verbs.vector_database import create_vector_db
from proscenium.verbs.vector_database import vector_db
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.know import knowledge_graph_client
from proscenium.verbs.vector_database import collection_name

from proscenium.scripts.graph_rag import (
    enrich_documents,
    load_knowledge_graph,
    load_entity_resolver,
    answer_question,
)

import demo.domains.legal as legal_config

app = typer.Typer(
    help="""
Graph extraction and question answering with GraphRAG on caselaw.
"""
)


@app.command(
    help=f"Enrich documents from {legal_config.hf_dataset_id} and write to {legal_config.enrichment_jsonl_file}."
)
def enrich():

    enrich_documents(
        legal_config.retrieve_documents,
        legal_config.doc_as_rich,
        legal_config.enrichment_jsonl_file,
        legal_config.default_chunk_extraction_model_id,
        legal_config.chunk_extraction_template,
        legal_config.LegalOpinionChunkExtractions,
        legal_config.doc_enrichments,
    )


@app.command(
    help=f"Load enrichments from {legal_config.enrichments_jsonl_file} into the knowledge graph."
)
def load_graph():

    driver = knowledge_graph_client(
        legal_config.neo4j_uri, legal_config.neo4j_username, legal_config.neo4j_password
    )

    load_knowledge_graph(
        driver,
        legal_config.enrichments_jsonl_file,
        legal_config.LegalOpinionEnrichments,
        legal_config.doc_enrichments_to_graph,
    )

    driver.close()


@app.command(help="Show the knowledge graph as stored in the graph db.")
def show_graph():

    driver = knowledge_graph_client(
        legal_config.neo4j_uri, legal_config.neo4j_username, legal_config.neo4j_password
    )

    legal_config.show_knowledge_graph(driver)

    driver.close()


@app.command(help="Load the vector db used for entity resolution.")
def load_resolver():
    embedding_fn = embedding_function(legal_config.embedding_model_id)
    print("Embedding model", legal_config.embedding_model_id)

    vector_db_client = create_vector_db(
        legal_config.milvus_uri, embedding_fn, overwrite=True
    )
    print("Vector db stored at", legal_config.milvus_uri)

    driver = knowledge_graph_client(
        legal_config.neo4j_uri, legal_config.neo4j_username, legal_config.neo4j_password
    )

    load_entity_resolver(driver, vector_db_client, embedding_fn, collection_name)

    driver.close()
    vector_db_client.close()


@app.command(
    help="Ask a legal question using the knowledge graph and entity resolver established in the previous steps."
)
def ask():

    vector_db_client = vector_db(legal_config.milvus_uri)
    print(
        "Connected to vector db stored at",
        legal_config.milvus_uri,
        "with embedding model",
        legal_config.embedding_model_id,
    )
    print("\n")

    driver = knowledge_graph_client(
        legal_config.neo4j_uri, legal_config.neo4j_username, legal_config.neo4j_password
    )

    question = legal_config.user_question()

    answer = answer_question(
        question,
        legal_config.default_query_extraction_model_id,
        vector_db_client,
        legal_config.embedding_model_id,
        driver,
        legal_config.default_generation_model_id,
        legal_config.query_extract,
        legal_config.extract_to_context,
        legal_config.context_to_prompts,
    )

    if answer:
        print(Panel(answer, title="Answer"))
    else:
        print("No answer")

    driver.close()
    vector_db_client.close()
