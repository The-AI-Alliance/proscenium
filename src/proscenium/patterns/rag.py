from typing import List, Dict

import logging
from rich.table import Table

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.complete import complete_simple

log = logging.getLogger(__name__)

rag_system_prompt = "Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer."

rag_prompt_template = """
The document chunks that are most similar to the query are:

{context}

Question:

{query}

Answer:
"""


def rag_prompt(chunks: List[Dict], query: str) -> str:

    context = "\n\n".join(
        [
            f"CHUNK {chunk['id']}. {chunk['entity']['text']}"
            for i, chunk in enumerate(chunks)
        ]
    )

    return rag_prompt_template.format(context=context, query=query)


def closest_chunks(
    client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    query: str,
    collection_name: str,
    k: int = 4,
) -> List[Dict]:

    client.load_collection(collection_name)

    result = client.search(
        collection_name=collection_name,
        data=embedding_fn.encode_queries([query]),
        anns_field="vector",
        search_params={"metric": "IP", "offset": 0},
        output_fields=["text"],
        limit=k,
    )

    hits = result[0]

    return hits


def chunk_hits_table(chunks: list[dict]) -> Table:

    table = Table(title="Closest Chunks", show_lines=True)
    table.add_column("id", justify="right")
    table.add_column("distance")
    table.add_column("entity.text", justify="right")
    for chunk in chunks:
        table.add_row(str(chunk["id"]), str(chunk["distance"]), chunk["entity"]["text"])
    return table


def answer_question(
    query: str,
    model_id: str,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str,
) -> str:

    chunks = closest_chunks(vector_db_client, embedding_fn, query, collection_name)
    log.info("Found %s closest chunks", len(chunks))
    log.info(chunk_hits_table(chunks))

    prompt = rag_prompt(chunks, query)
    log.info("RAG prompt created. Calling inference at %s", model_id)

    answer = complete_simple(model_id, rag_system_prompt, prompt)

    return answer
