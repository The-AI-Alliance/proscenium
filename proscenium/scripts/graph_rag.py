from typing import List
from typing import Callable
from typing import Any

import time
from langchain_core.documents.base import Document
from neo4j import Driver
import csv

from rich import print
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.chunk import documents_to_chunks_by_tokens
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.display.neo4j import triples_table, pairs_table
from proscenium.verbs.display.milvus import collection_panel

extraction_system_prompt = "You are an entity extractor"


def extract_triples_from_document(
    doc: Document,
    doc_as_rich: Callable[[Document], Panel],
    doc_direct_triples: Callable[[Document], list[tuple[str, str, str]]],
    chunk_extraction_model_id: str,
    triples_from_chunk: Callable[[str, Document, Document], List[tuple[str, str, str]]],
) -> List[tuple[str, str, str]]:

    print(doc_as_rich(doc))
    print()

    doc_triples = []

    direct_triples = doc_direct_triples(doc)
    doc_triples.extend(direct_triples)

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        new_triples = triples_from_chunk(chunk_extraction_model_id, chunk, doc)

        print("Found", len(new_triples), "triples in chunk", i + 1, "of", len(chunks))

        doc_triples.extend(new_triples)

    return doc_triples


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


def find_matching_objects(
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    question_triples: List[tuple[str, str, str]],
) -> List[tuple[str, str]]:

    subject_predicate_pairs = []
    for triple in question_triples:
        print("Finding entity matches for", triple[0], "(", triple[1], ")")
        subject, predicate, object = triple
        # TODO apply distance threshold
        hits = closest_chunks(vector_db_client, embedding_fn, subject, k=5)
        for match in [head["entity"]["text"] for head in hits[:1]]:
            print("   match:", match)
            subject_predicate_pairs.append((match, predicate))
    # Note: the above block loses the tie-back link from the match to the original triple

    return subject_predicate_pairs


def extract_entities(
    retrieve_documents: Callable[[], List[Document]],
    doc_as_rich: Callable[[Document], Panel],
    entity_csv: str,
    doc_direct_triples: Callable[[Document], list[tuple[str, str, str]]],
    chunk_extraction_model_id: str,
    triples_from_chunk: Callable[[Document, Document], List[tuple[str, str, str]]],
) -> None:

    docs = retrieve_documents()

    with Progress() as progress:

        task_extract = progress.add_task(
            "[green]Extracting entities...", total=len(docs)
        )

        with open(entity_csv, "wt") as f:

            writer = csv.writer(f, delimiter=",", quotechar='"')
            writer.writerow(["subject", "predicate", "object"])  # header

            for doc in docs:

                doc_triples = extract_triples_from_document(
                    doc,
                    doc_as_rich,
                    doc_direct_triples,
                    chunk_extraction_model_id,
                    triples_from_chunk,
                )

                writer.writerows(doc_triples)
                progress.update(task_extract, advance=1)
                time.sleep(1)  # TODO remove this hard-coded rate limiter

        print("Wrote entity triples to", entity_csv)


def load_entity_graph(
    driver: Driver, entity_csv: str, add_triple: Callable[[Any, str, str, str], None]
) -> None:

    print("Parsing triples from", entity_csv)

    with open(entity_csv) as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        next(reader, None)  # skip header row
        triples = [row for row in reader]

        with Progress() as progress:

            task_load = progress.add_task(
                f"[green]Loading {len(triples)} triples into graph...",
                total=len(triples),
            )

            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")  # empty graph
                for subject, predicate, object in triples:
                    session.execute_write(add_triple, subject, predicate, object)
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
    triples_from_query: Callable[[str, str, str], List[tuple[str, str, str]]],
    generation_prompts: Callable[[str, List[tuple[str, str, str]], Driver], str],
) -> str:

    print(Panel(question, title="Question"))

    question_entity_triples = triples_from_query(
        question, "", query_extraction_model_id
    )
    print("\n")
    if len(question_entity_triples) == 0:
        print("No triples extracted from question")
        return None
    print(triples_table(question_entity_triples, "Query Triples"))

    print("Finding entity matches for triples")
    embedding_fn = embedding_function(embedding_model_id)
    subject_predicate_pairs = find_matching_objects(
        vector_db_client, embedding_fn, question_entity_triples
    )
    print("\n")
    pairs_table(subject_predicate_pairs, "Subject Predicate Constraints")

    prompts = generation_prompts(question, subject_predicate_pairs, driver)

    if prompts is None:

        return None

    else:

        system_prompt, user_prompt = prompts

        response = complete_simple(
            generation_model_id, system_prompt, user_prompt, rich_output=True
        )

        return response
