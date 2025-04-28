from typing import List, Dict, Optional
import logging

from rich.console import Console

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.complete import complete_simple
from proscenium.verbs.display.milvus import chunk_hits_table
from proscenium.verbs.vector_database import closest_chunks


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


def answer_question(
    query: str,
    model_id: str,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str,
    console: Optional[Console] = None,
) -> str:

    chunks = closest_chunks(vector_db_client, embedding_fn, query, collection_name)
    logging.info("Found %s closest chunks", len(chunks))
    logging.info(chunk_hits_table(chunks))

    prompt = rag_prompt(chunks, query)
    logging.info("RAG prompt created. Calling inference at %s", model_id)

    answer = complete_simple(model_id, rag_system_prompt, prompt, console=console)

    return answer
