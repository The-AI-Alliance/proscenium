from typing import List
from typing import Callable
from typing import Any

import time
import json
from pydantic import BaseModel

from rich import print
from rich.panel import Panel
from rich.progress import Progress

from langchain_core.documents.base import Document
from neo4j import Driver

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.chunk import documents_to_chunks_by_tokens
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.extract import extract_to_pydantic_model
from proscenium.verbs.vector_database import closest_chunks
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.display.milvus import collection_panel


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

        ce = extract_to_pydantic_model(
            chunk_extraction_model_id,
            chunk_extraction_template,
            chunk_extract_clazz,
            chunk,
        )

        print("Extract model in chunk", i + 1, "of", len(chunks))
        print(Panel(str(ce)))

        extract_models.append(ce)

    return extract_models


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
    enrichments_jsonl_file: str,
    chunk_extraction_model_id: str,
    chunk_extraction_template: str,
    chunk_extract_clazz: type[BaseModel],
    doc_enrichments: Callable[[Document, list[BaseModel]], BaseModel],
) -> None:

    docs = retrieve_documents()

    with Progress() as progress:

        task_enrich = progress.add_task(
            "[green]Enriching documents...", total=len(docs)
        )

        with open(enrichments_jsonl_file, "wt") as f:

            for doc in docs:

                chunk_extract_models = extract_from_document_chunks(
                    doc,
                    doc_as_rich,
                    chunk_extraction_model_id,
                    chunk_extraction_template,
                    chunk_extract_clazz,
                )

                enrichments = doc_enrichments(doc, chunk_extract_models)
                enrichments_json = enrichments.model_dump_json()
                f.write(enrichments_json + "\n")

                progress.update(task_enrich, advance=1)
                time.sleep(1)  # TODO remove this hard-coded rate limiter

        print("Wrote document enrichments to", enrichments_jsonl_file)


def load_knowledge_graph(
    driver: Driver,
    enrichments_jsonl_file: str,
    enrichments_clazz: type[BaseModel],
    doc_enrichments_to_graph: Callable[[Any, BaseModel], None],
) -> None:

    print("Parsing enrichments from", enrichments_jsonl_file)

    enrichmentss = []
    with open(enrichments_jsonl_file, "r") as f:
        for line in f:
            e = enrichments_clazz.model_construct(**json.loads(line))
            enrichmentss.append(e)

    with Progress() as progress:

        task_load = progress.add_task(
            f"[green]Loading {len(enrichmentss)} enriched documents into graph...",
            total=len(enrichmentss),
        )

        with driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")  # empty graph
            for e in enrichmentss:
                session.execute_write(doc_enrichments_to_graph, e)
                progress.update(task_load, advance=1)

        driver.close()


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
