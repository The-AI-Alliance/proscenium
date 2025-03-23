
from typing import List
from typing import Dict
from typing import Callable
from typing import Any

from langchain_core.documents.base import Document
from neo4j import Driver
import csv

from rich import print
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress

from pydantic import BaseModel
from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.chunk import documents_to_chunks_by_tokens
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.read import load_hugging_face_dataset
from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.display.neo4j import triples_table, pairs_table
from proscenium.verbs.display.milvus import collection_panel

extraction_system_prompt = "You are an entity extractor"

def extract_triples_from_document(
    doc: Document,
    model_id: str,
    extraction_template: str,
    doc_as_rich: Callable[[Document], Panel],
    doc_as_object: Callable[[Document], str],
    doc_direct_triples: Callable[[Document], list[tuple[str, str, str]]],
    extraction_model: BaseModel,
    get_triples_from_extract: Callable[[BaseModel, str], List[tuple[str, str, str]]],
    ) -> List[tuple[str, str, str]]:

    print(doc_as_rich(doc))
    print()

    doc_triples = []

    direct_triples = doc_direct_triples(doc)
    doc_triples.extend(direct_triples)

    object = doc_as_object(doc)

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        extract = complete_simple(
            model_id,
            extraction_system_prompt,
            extraction_template.format(text = chunk.page_content),
            response_format = {
                "type": "json_object",
                "schema": extraction_model.model_json_schema(),
            },
            rich_output = True)

        new_triples = get_triples_from_extract(extract, object)

        print("Found", len(new_triples), "triples in chunk", i+1, "of", len(chunks))

        doc_triples.extend(new_triples)

    return doc_triples

def full_doc_by_id(
        name: str,
        hf_dataset_id: str,
        hf_dataset_column: str,
        num_docs: int,
        doc_as_object: Callable[[Document], str]) -> Document:

    documents = load_hugging_face_dataset(
        hf_dataset_id,
        page_content_column = hf_dataset_column)

    print("Searching the first", num_docs,
        " documents of", len(documents),
        "in", hf_dataset_id, "column", hf_dataset_column)

    documents = documents[:num_docs]

    # TODO build this earlier and persist in graph
    doc_object_to_index = {
        doc_as_object(doc): i for i, doc in enumerate(documents)}

    return documents[doc_object_to_index[name]]

def query_for_objects(
    driver: Driver,
    subject_predicate_constraints: List[tuple[str, str]],
    matching_objects_query: Callable[[List[tuple[str, str]]], str]
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
    question_triples: List[tuple[str, str, str]]
    ) -> List[tuple[str, str]]:

    subject_predicate_pairs = []
    for triple in question_triples:
        print("Finding entity matches for", triple[0], "(", triple[1], ")")
        subject, predicate, object = triple
        # TODO apply distance threshold
        hits = closest_chunks(vector_db_client, embedding_fn, subject, k=5)
        for match in [head['entity']['text'] for head in hits[:1]]:
            print("   match:", match)
            subject_predicate_pairs.append((match, predicate))
    # Note: the above block loses the tie-back link from the match to the original triple

    return subject_predicate_pairs

def extract_entities(
    hf_dataset_id: str,
    hf_dataset_column: str,
    num_docs: int,
    entity_csv: str,
    model_id: str,
    extraction_template: str,
    doc_as_rich: Callable[[Document], Panel],
    doc_as_object: Callable[[Document], str],
    doc_direct_triples: Callable[[Document], list[tuple[str, str, str]]],
    extraction_model: BaseModel,
    get_triples_from_extract: Callable[[BaseModel, str], List[tuple[str, str, str]]]
    ) -> None:

    docs = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)

    old_len = len(docs)
    docs = docs[:num_docs]
    print("using the first", num_docs, "documents of", old_len, "from HF dataset", hf_dataset_id)

    with Progress() as progress:

        task_extract = progress.add_task("[green]Extracting entities...", total=len(docs))

        with open(entity_csv, "wt") as f:

            writer = csv.writer(f, delimiter=",", quotechar='"')
            writer.writerow(["subject", "predicate", "object"]) # header

            for doc in docs:

                doc_triples = extract_triples_from_document(
                    doc,
                    model_id,
                    extraction_template,
                    doc_as_rich,
                    doc_as_object,
                    doc_direct_triples,
                    extraction_model,
                    get_triples_from_extract)

                writer.writerows(doc_triples)
                progress.update(task_extract, advance=1)

        print("Wrote entity triples to", entity_csv)

def load_entity_graph(
    driver: Driver,
    entity_csv: str,
    add_triple: Callable[[Any, str, str, str], None]
) -> None:

    print("Parsing triples from", entity_csv)

    with open(entity_csv) as f:
        reader = csv.reader(f, delimiter=",", quotechar='"')
        next(reader, None)  # skip header row
        triples = [row for row in reader]

        with Progress() as progress:

            task_load = progress.add_task(f"[green]Loading {len(triples)} triples into graph...", total=len(triples))

            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n") # empty graph
                for subject, predicate, object in triples:
                    session.execute_write(add_triple, subject, predicate, object)
                    progress.update(task_load, advance=1)

            driver.close()

def show_entity_graph(driver: Driver):

    with driver.session() as session:

        result = session.run("MATCH ()-[r]->() RETURN type(r) AS rel") # all relationships
        relations = [record["rel"] for record in result]
        unique_relations = list(set(relations))
        table = Table(title="Relationship Types", show_lines=False)
        table.add_column("Relationship Type", justify="left", style="blue")
        for r in unique_relations:
            table.add_row(r)
        print(table)

        result = session.run("MATCH (n) RETURN n.name AS name") # all nodes
        table = Table(title="Nodes", show_lines=False)
        table.add_column("Node Name", justify="left", style="green")
        for record in result:
            table.add_row(record['name'])
        print(table)

        for r in unique_relations:
            cypher = f"MATCH (s)-[:{r}]->(o) RETURN s.name, o.name"
            result = session.run(cypher)
            table = Table(title=f"Relation: {r}", show_lines=False)
            table.add_column("Subject Name", justify="left", style="blue")
            table.add_column("Object Name", justify="left", style="purple")
            for record in result:
                table.add_row(record['s.name'], record['o.name'])
            print(table)

def load_entity_resolver(
    driver: Driver,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str) -> None:

    names = []
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN n.name AS name")
        new_names = [Document(record["name"]) for record in result]
        names.extend(new_names)

    info = add_chunks_to_vector_db(vector_db_client, embedding_fn, names)
    print(info['insert_count'], "chunks inserted")
    print(collection_panel(vector_db_client, collection_name))

def answer_question(
    question: str,
    hf_dataset_id: str,
    hf_dataset_column: str,
    num_docs: int,
    doc_as_object: Callable[[Document], str],
    generation_model_id: str,
    system_prompt: str,
    graphrag_prompt_template: str,
    driver: Driver,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    query_extraction_template: str,
    query_extraction_model_id: str,
    query_extraction_data_model: BaseModel,
    get_triples_from_query_extract: Callable[[BaseModel, str], List[tuple[str, str, str]]],
    matching_objects_query: Callable[[List[tuple[str, str]]], str],
    ) -> str:

    print(Panel(question, title="Question"))

    extract = complete_simple(
        query_extraction_model_id,
        extraction_system_prompt,
        query_extraction_template.format(text = question),
        response_format = {
            "type": "json_object",
            "schema": query_extraction_data_model.model_json_schema(),
        },
        rich_output = True)

    print("\nExtracting triples from extraction response")
    question_entity_triples = get_triples_from_query_extract(extract, "")
    print("\n")
    if len(question_entity_triples) == 0:
        print("No triples extracted from question")
        return None
    print(triples_table(question_entity_triples, "Query Triples"))

    print("Finding entity matches for triples")
    subject_predicate_pairs = find_matching_objects(vector_db_client, embedding_fn, question_entity_triples)
    print("\n")
    pairs_table(subject_predicate_pairs, "Subject Predicate Constraints")

    print("Querying for objects that match those constraints")
    object_names = query_for_objects(driver, subject_predicate_pairs, matching_objects_query)
    print("Objects with names:", object_names, "are matches for", subject_predicate_pairs)

    if len(object_names) > 0:

        doc = full_doc_by_id(object_names[0], hf_dataset_id, hf_dataset_column, num_docs, doc_as_object)

        user_prompt = graphrag_prompt_template.format(
            document_text = doc.page_content,
            question = question)

        response = complete_simple(
            generation_model_id,
            system_prompt,
            user_prompt,
            rich_output = True)

        return response

    else:

        print("No objects found for entity role pairs")
        return None
