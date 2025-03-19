
import typer
from rich import print
from rich.panel import Panel

from proscenium.verbs.know import knowledge_graph_client
from proscenium.verbs.vector_database import create_vector_db
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db
from proscenium.verbs.know import knowledge_graph_client
from proscenium.verbs.vector_database import collection_name

from proscenium.scripts.graph_rag import extract_entities, \
    load_entity_graph, show_entity_graph, load_entity_resolver, \
    answer_question

import proscenium.typer.config_graph_rag as config

app = typer.Typer()

@app.command()
def extract():

    extract_entities(
        config.hf_dataset_id,
        config.hf_dataset_column,
        config.num_docs,
        config.entity_csv_file,
        config.model_id,
        config.extraction_template,
        config.doc_as_rich,
        config.doc_as_object,
        config.doc_direct_triples,
        config.predicates)

@app.command()
def load_graph():

    driver = knowledge_graph_client(
        config.neo4j_uri,
        config.neo4j_username,
        config.neo4j_password)

    load_entity_graph(
        driver,
        config.entity_csv_file,
        config.add_triple)

    driver.close()

@app.command()
def show_graph():

    driver = knowledge_graph_client(
        config.neo4j_uri,
        config.neo4j_username,
        config.neo4j_password)

    show_entity_graph(driver)

    driver.close()

@app.command()
def load_resolver():
    embedding_fn = embedding_function(config.embedding_model_id)
    print("Embedding model", config.embedding_model_id)

    vector_db_client = create_vector_db(config.milvus_uri, embedding_fn, overwrite=True)
    print("Vector db stored at", config.milvus_uri)

    driver = knowledge_graph_client(
        config.neo4j_uri,
        config.neo4j_username,
        config.neo4j_password)

    load_entity_resolver(driver, vector_db_client, embedding_fn, collection_name)

    driver.close()
    vector_db_client.close()


@app.command()
def ask():

    embedding_fn = embedding_function(config.embedding_model_id)
    vector_db_client = vector_db(config.milvus_uri)
    print("Connected to vector db stored at", config.milvus_uri, "with embedding model", config.embedding_model_id)
    print("\n")

    driver = knowledge_graph_client(
        config.neo4j_uri,
        config.neo4j_username,
        config.neo4j_password)

    question = config.get_user_question()

    answer = answer_question(
        question,
        config.hf_dataset_id,
        config.hf_dataset_column,
        config.num_docs,
        config.doc_as_object,
        config.model_id,
        config.extraction_template,
        config.system_prompt,
        config.graphrag_prompt_template,
        driver,
        vector_db_client,
        embedding_fn,
        config.matching_objects_query,
        config.predicates)

    if answer:
        print(Panel(answer, title="Answer"))
    else:
        print("No answer")

    driver.close()
    vector_db_client.close()
