
import typer
from rich import print
from rich.panel import Panel

from proscenium.verbs.vector_database import create_vector_db
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db
from proscenium.verbs.know import knowledge_graph_client
from proscenium.verbs.vector_database import collection_name

from proscenium.scripts.graph_rag import extract_entities, \
    load_entity_graph, show_entity_graph, load_entity_resolver, \
    answer_question

import demo.domains.legal as legal_config

app = typer.Typer()

@app.command()
def extract():

    extract_entities(
        legal_config.retrieve_documents,
        legal_config.doc_as_rich,
        legal_config.entity_csv_file,
        legal_config.doc_direct_triples,
        legal_config.default_chunk_extraction_model_id,
        legal_config.get_triples_from_chunk)

@app.command()
def load_graph():

    driver = knowledge_graph_client(
        legal_config.neo4j_uri,
        legal_config.neo4j_username,
        legal_config.neo4j_password)

    load_entity_graph(
        driver,
        legal_config.entity_csv_file,
        legal_config.add_triple)

    driver.close()

@app.command()
def show_graph():

    driver = knowledge_graph_client(
        legal_config.neo4j_uri,
        legal_config.neo4j_username,
        legal_config.neo4j_password)

    show_entity_graph(driver)

    driver.close()

@app.command()
def load_resolver():
    embedding_fn = embedding_function(legal_config.embedding_model_id)
    print("Embedding model", legal_config.embedding_model_id)

    vector_db_client = create_vector_db(legal_config.milvus_uri, embedding_fn, overwrite=True)
    print("Vector db stored at", legal_config.milvus_uri)

    driver = knowledge_graph_client(
        legal_config.neo4j_uri,
        legal_config.neo4j_username,
        legal_config.neo4j_password)

    load_entity_resolver(driver, vector_db_client, embedding_fn, collection_name)

    driver.close()
    vector_db_client.close()


@app.command()
def ask():

    embedding_fn = embedding_function(legal_config.embedding_model_id)
    vector_db_client = vector_db(legal_config.milvus_uri)
    print("Connected to vector db stored at", legal_config.milvus_uri, "with embedding model", legal_config.embedding_model_id)
    print("\n")

    driver = knowledge_graph_client(
        legal_config.neo4j_uri,
        legal_config.neo4j_username,
        legal_config.neo4j_password)

    question = legal_config.get_user_question()

    answer = answer_question(
        question,
        legal_config.retrieve_document,
        legal_config.default_generation_model_id,
        legal_config.system_prompt,
        legal_config.graphrag_prompt_template,
        driver,
        vector_db_client,
        embedding_fn,
        legal_config.query_extraction_template,
        legal_config.query_extraction_model_id,
        legal_config.query_extraction_data_model,
        legal_config.get_triples_from_query_extract,
        legal_config.matching_objects_query,
        )

    if answer:
        print(Panel(answer, title="Answer"))
    else:
        print("No answer")

    driver.close()
    vector_db_client.close()
