from typing import List
from typing import Callable
from typing import Any

import logging
import time
import json
from pydantic import BaseModel

from rich import print
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from langchain_core.documents.base import Document
from neo4j import Driver

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.chunk import documents_to_chunks_by_tokens
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.display.milvus import collection_panel

extraction_system_prompt = "You are an entity extractor"


def extract_from_document_chunks(
    doc: Document,
    doc_as_rich: Callable[[Document], Panel],
    chunk_extraction_model_id: str,
    chunk_extraction_template: str,
    chunk_extract_clazz: type[BaseModel],
) -> List[BaseModel]:

    print(doc_as_rich(doc))
    print()

    extract_models = []

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        ce = chunk_extract(
            chunk_extraction_model_id,
            chunk_extraction_template,
            chunk_extract_clazz,
            chunk,
        )

        print("Extract model in chunk", i + 1, "of", len(chunks))
        print(Panel(str(ce)))

        extract_models.append(ce)

    return extract_models


def query_for_objects(
    driver: Driver,
    subject_predicate_constraints: List[tuple[str, str]],
    matching_objects_query: Callable[[List[tuple[str, str]]], str],
) -> List[str]:
    with driver.session() as session:
        query = matching_objects_query(subject_predicate_constraints)
        print(Panel(query, title="Cypher Query"))
        result = session.run(query)
        objects = []
        print("   Result:")
        for record in result:
            objects.append(record["name"])
            print(record["name"])
        return objects


def chunk_extract(
    chunk_extraction_model_id: str,
    chunk_extraction_template: str,
    clazz: type[BaseModel],
    chunk: Document,
) -> BaseModel:

    extract_str = complete_simple(
        chunk_extraction_model_id,
        extraction_system_prompt,
        chunk_extraction_template.format(text=chunk.page_content),
        response_format={
            "type": "json_object",
            "schema": clazz.model_json_schema(),
        },
        rich_output=True,
    )

    logging.info("chunk_extract: extract_str = <<<%s>>>", extract_str)

    try:
        extract_dict = json.loads(extract_str)
        return clazz.model_construct(**extract_dict)
    except Exception as e:
        logging.error("chunk_extract: Exception: %s", e)

    return None


def find_matching_objects(
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    question_triples: List[tuple[str, str, str]],
) -> List[tuple[str, str]]:

    subject_predicate_pairs = []
    for triple in question_triples:
        print("Finding entity matches for", triple[0], "(", triple[1], ")")
        subject, predicate, obj = triple
        # TODO apply distance threshold
        hits = closest_chunks(vector_db_client, embedding_fn, subject, k=5)
        for match in [head["entity"]["text"] for head in hits[:1]]:
            print("   match:", match)
            subject_predicate_pairs.append((match, predicate))
    # Note: the above block loses the tie-back link from the match to the original triple

    return subject_predicate_pairs


def enrich_documents(
    retrieve_documents: Callable[[], List[Document]],
    doc_as_rich: Callable[[Document], Panel],
    entity_jsonl_file: str,
    chunk_extraction_model_id: str,
    chunk_extraction_template: str,
    chunk_extract_clazz: type[BaseModel],
    doc_enrichments: Callable[[Document, list[BaseModel]], dict],
) -> None:

    docs = retrieve_documents()

    with Progress() as progress:

        task_extract = progress.add_task(
            "[green]Extracting entities...", total=len(docs)
        )

        with open(entity_jsonl_file, "wt") as f:

            for doc in docs:

                chunk_extract_models = extract_from_document_chunks(
                    doc,
                    doc_as_rich,
                    chunk_extraction_model_id,
                    chunk_extraction_template,
                    chunk_extract_clazz,
                )

                enrichments = doc_enrichments(doc, chunk_extract_models)
                extract_json = json.dumps(enrichments, ensure_ascii=False)
                f.write(extract_json + "\n")

                progress.update(task_extract, advance=1)
                time.sleep(1)  # TODO remove this hard-coded rate limiter

        print("Wrote entity triples to", entity_jsonl_file)


def load_entity_graph(
    driver: Driver,
    entity_jsonl_file: str,
    add_row_to_graph: Callable[[Any, str, str, str], None],
) -> None:

    print("Parsing triples from", entity_jsonl_file)

    rows = []
    with open(entity_jsonl_file, "r") as f:
        for line in f:
            rows.append(json.loads(line))

    with Progress() as progress:

        task_load = progress.add_task(
            f"[green]Loading {len(rows)} triples into graph...",
            total=len(rows),
        )

        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")  # empty graph
            for row in rows:
                session.execute_write(add_row_to_graph, row)
                progress.update(task_load, advance=1)

        driver.close()


def show_entity_graph(driver: Driver):

    with driver.session() as session:

        result = session.run(
            "MATCH ()-[r]->() RETURN type(r) AS rel"
        )  # all relationships
        relations = [record["rel"] for record in result]
        unique_relations = list(set(relations))
        table = Table(title="Relationship Types", show_lines=False)
        table.add_column("Relationship Type", justify="left", style="blue")
        for r in unique_relations:
            table.add_row(r)
        print(table)

        result = session.run("MATCH (n) RETURN n.name AS name")  # all nodes
        table = Table(title="Nodes", show_lines=False)
        table.add_column("Node Name", justify="left", style="green")
        for record in result:
            table.add_row(record["name"])
        print(table)

        for r in unique_relations:
            cypher = f"MATCH (s)-[:{r}]->(o) RETURN s.name, o.name"
            result = session.run(cypher)
            table = Table(title=f"Relation: {r}", show_lines=False)
            table.add_column("Subject Name", justify="left", style="blue")
            table.add_column("Object Name", justify="left", style="purple")
            for record in result:
                table.add_row(record["s.name"], record["o.name"])
            print(table)


def load_entity_resolver(
    driver: Driver,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str,
) -> None:

    names = []
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN n.name AS name")
        new_names = [Document(record["name"]) for record in result]
        names.extend(new_names)

    info = add_chunks_to_vector_db(vector_db_client, embedding_fn, names)
    print(info["insert_count"], "chunks inserted")
    print(collection_panel(vector_db_client, collection_name))


def answer_question(
    question: str,
    query_extraction_model_id: str,
    vector_db_client: MilvusClient,
    embedding_model_id: str,
    driver: Driver,
    generation_model_id: str,
    query_extract: Callable[
        [str, str], BaseModel
    ],  # (query_str, query_extraction_model_id) -> QueryExtractions
    extract_to_context: Callable[
        [BaseModel, str, Driver, MilvusClient], BaseModel
    ],  # (QueryExtractions, query_str, Driver, MilvusClient) -> Context
    context_to_prompts: Callable[
        [BaseModel], tuple[str, str]
    ],  # Context -> (system_prompt, user_prompt)
) -> str:

    print(Panel(question, title="Question"))

    print("Extracting information from the question")
    extract = query_extract(question, query_extraction_model_id)
    if extract is None:
        print("Unable to extract information from that question")
        return None
    print("Extract:", extract)

    print("Forming context from the extracted information")
    context = extract_to_context(
        extract, question, driver, vector_db_client, embedding_model_id
    )
    print("Context:", context)

    prompts = context_to_prompts(context, generation_model_id)

    if prompts is None:

        return None

    else:

        system_prompt, user_prompt = prompts

        response = complete_simple(
            generation_model_id, system_prompt, user_prompt, rich_output=True
        )

        return response
