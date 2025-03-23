
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

from proscenium.typer import graph_rag_config

app = typer.Typer()

@app.command()
def extract():

    extract_entities(
        graph_rag_config.hf_dataset_id,
        graph_rag_config.hf_dataset_column,
        graph_rag_config.num_docs,
        graph_rag_config.entity_csv_file,
        graph_rag_config.extraction_model_id,
        graph_rag_config.extraction_template,
        graph_rag_config.doc_as_rich,
        graph_rag_config.doc_as_object,
        graph_rag_config.doc_direct_triples,
        graph_rag_config.extraction_model,
        graph_rag_config.get_triples_from_extract)

@app.command()
def load_graph():

    driver = knowledge_graph_client(
        graph_rag_config.neo4j_uri,
        graph_rag_config.neo4j_username,
        graph_rag_config.neo4j_password)

    load_entity_graph(
        driver,
        graph_rag_config.entity_csv_file,
        graph_rag_config.add_triple)

    driver.close()

@app.command()
def show_graph():

    driver = knowledge_graph_client(
        graph_rag_config.neo4j_uri,
        graph_rag_config.neo4j_username,
        graph_rag_config.neo4j_password)

    show_entity_graph(driver)

    driver.close()

@app.command()
def load_resolver():
    embedding_fn = embedding_function(graph_rag_config.embedding_model_id)
    print("Embedding model", graph_rag_config.embedding_model_id)

    vector_db_client = create_vector_db(graph_rag_config.milvus_uri, embedding_fn, overwrite=True)
    print("Vector db stored at", graph_rag_config.milvus_uri)

    driver = knowledge_graph_client(
        graph_rag_config.neo4j_uri,
        graph_rag_config.neo4j_username,
        graph_rag_config.neo4j_password)

    load_entity_resolver(driver, vector_db_client, embedding_fn, collection_name)

    driver.close()
    vector_db_client.close()


@app.command()
def ask():

    embedding_fn = embedding_function(graph_rag_config.embedding_model_id)
    vector_db_client = vector_db(graph_rag_config.milvus_uri)
    print("Connected to vector db stored at", graph_rag_config.milvus_uri, "with embedding model", graph_rag_config.embedding_model_id)
    print("\n")

    driver = knowledge_graph_client(
        graph_rag_config.neo4j_uri,
        graph_rag_config.neo4j_username,
        graph_rag_config.neo4j_password)

    question = graph_rag_config.get_user_question()

    answer = answer_question(
        question,
        graph_rag_config.hf_dataset_id,
        graph_rag_config.hf_dataset_column,
        graph_rag_config.num_docs,
        graph_rag_config.doc_as_object,
        graph_rag_config.generation_model_id,
        graph_rag_config.extraction_template,
        graph_rag_config.system_prompt,
        graph_rag_config.graphrag_prompt_template,
        driver,
        vector_db_client,
        embedding_fn,
        graph_rag_config.matching_objects_query,
        graph_rag_config.extraction_model_id,
        graph_rag_config.extraction_model,
        graph_rag_config.get_triples_from_extract)

    if answer:
        print(Panel(answer, title="Answer"))
    else:
        print("No answer")

    driver.close()
    vector_db_client.close()
