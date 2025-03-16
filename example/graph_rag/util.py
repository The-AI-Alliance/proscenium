
from typing import List

from langchain_core.documents.base import Document
from neo4j import Driver
import csv

from rich import print
from rich.panel import Panel
from rich.progress import Progress

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.parse import PartialFormatter
from proscenium.parse import get_triples_from_extract
from proscenium.parse import raw_extraction_template
from proscenium.parse import get_triples_from_extract
from proscenium.chunk import documents_to_chunks_by_tokens
from proscenium.complete import complete_simple
from proscenium.read import load_hugging_face_dataset
from proscenium.vector_database import closest_chunks
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.display.neo4j import triples_table, pairs_table
from proscenium.display.milvus import collection_panel

# Problem-specific configuration:
import example.graph_rag.config as config
import example.graph_rag.util as util

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in config.predicates.items()]))

extraction_system_prompt = "You are an entity extractor"

def extract_triples_from_document(
    doc: Document
    ) -> List[tuple[str, str, str]]:

    print(config.doc_as_rich(doc))
    print()

    doc_triples = []

    direct_triples = config.doc_direct_triples(doc)
    doc_triples.extend(direct_triples)

    object = config.doc_as_object(doc)

    chunks = documents_to_chunks_by_tokens([doc], chunk_size=1000, chunk_overlap=0)
    for i, chunk in enumerate(chunks):

        extract = complete_simple(
            config.model_id,
            util.extraction_system_prompt,
            extraction_template.format(text = chunk.page_content),
            rich_output = True)

        new_triples = get_triples_from_extract(extract, object, config.predicates)

        print("Found", len(new_triples), "triples in chunk", i+1, "of", len(chunks))

        doc_triples.extend(new_triples)

    return doc_triples

def full_doc_by_id(name: str) -> Document:

    documents = load_hugging_face_dataset(
        config.hf_dataset_id,
        page_content_column = config.hf_dataset_column)

    print("Searching the first", config.num_docs,
        " documents of", len(documents),
        "in", config.hf_dataset_id, "column", config.hf_dataset_column)

    documents = documents[:config.num_docs]

    # TODO build this earlier and persist in graph
    doc_object_to_index = {
        config.doc_as_object(doc): i for i, doc in enumerate(documents)}

    return documents[doc_object_to_index[name]]

def query_for_objects(
    driver: Driver,
    subject_predicate_constraints: List[tuple[str, str]]
    ) -> List[str]:
    with driver.session() as session:
        query = config.matching_objects_query(subject_predicate_constraints)
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
    entity_csv: str
) -> None:

    docs = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)

    old_len = len(docs)
    docs = docs[:config.num_docs]
    print("using the first", config.num_docs, "documents of", old_len, "from HF dataset", hf_dataset_id)

    with Progress() as progress:

        task_extract = progress.add_task("[green]Extracting entities...", total=len(docs))

        with open(entity_csv, "wt") as f:

            writer = csv.writer(f, delimiter=",", quotechar='"')
            writer.writerow(["subject", "predicate", "object"]) # header

            for doc in docs:

                doc_triples = extract_triples_from_document(doc)
                writer.writerows(doc_triples)
                progress.update(task_extract, advance=1)

        print("Wrote entity triples to", entity_csv)

def load_entity_graph(
    entity_csv: str,
    driver: Driver) -> None:

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
                    session.execute_write(config.add_triple, subject, predicate, object)
                    progress.update(task_load, advance=1)

            driver.close()

def load_entity_resolver(
    driver: Driver,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbedding,
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
    driver: Driver,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction
) -> str:

    print(Panel(question, title="Question"))

    extraction_response = complete_simple(
        config.model_id,
        util.extraction_system_prompt,
        util.extraction_template.format(text = question),
        rich_output = True)

    print("\nExtracting triples from extraction response")
    question_entity_triples = get_triples_from_extract(extraction_response, "", config.predicates)
    print("\n")
    if len(question_entity_triples) == 0:
        print("No triples extracted from question")
        return None
    print(triples_table(question_entity_triples, "Query Triples"))

    print("Finding entity matches for triples")
    subject_predicate_pairs = util.find_matching_objects(vector_db_client, embedding_fn, question_entity_triples)
    print("\n")
    pairs_table(subject_predicate_pairs, "Subject Predicate Constraints")

    print("Querying for objects that match those constraints")
    object_names = util.query_for_objects(driver, subject_predicate_pairs)
    print("Objects with names:", object_names, "are matches for", subject_predicate_pairs)

    if len(object_names) > 0:

        doc = util.full_doc_by_id(object_names[0])

        user_prompt = config.graphrag_prompt_template.format(
            case_text = doc.page_content,
            question = question)

        response = complete_simple(
            config.model_id,
            config.system_prompt,
            user_prompt,
            rich_output = True)

        return response

    else:

        print("No objects found for entity role pairs")
        return None
