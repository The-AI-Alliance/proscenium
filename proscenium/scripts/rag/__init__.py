
from typing import List, Dict

from rich import print
from rich.panel import Panel

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.complete import complete_simple
from proscenium.display.milvus import chunk_hits_table
from proscenium.vector_database import closest_chunks
from proscenium.read import load_file
from proscenium.chunk import documents_to_chunks_by_characters
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import collection_name
from proscenium.display.milvus import collection_panel

def build_vector_db(
    data_file: str,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction):

    documents = load_file(data_file)
    chunks = documents_to_chunks_by_characters(documents)
    print("Data file", data_file, "has", len(chunks), "chunks")

    info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
    print(info['insert_count'], "chunks inserted")
    print(collection_panel(vector_db_client, collection_name))

rag_system_prompt = "Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer."

rag_prompt_template = """
The document chunks that are most similar to the query are:

{context}

Question:

{query}

Answer:
"""

def rag_prompt(
    chunks: List[Dict],
    query: str
) -> str:

    context = "\n\n".join([f"CHUNK {chunk['id']}. {chunk['entity']['text']}" for i, chunk in enumerate(chunks)])

    return rag_prompt_template.format(context=context, query=query)


def answer_question(
    query: str,
    model_id: str,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction) -> str:

    print(Panel(query, title="User"))

    chunks = closest_chunks(vector_db_client, embedding_fn, query)
    print("Found", len(chunks), "closest chunks")
    print(chunk_hits_table(chunks))

    prompt = rag_prompt(chunks, query)
    print("RAG prompt created. Calling inference at", model_id,"\n\n")

    answer = complete_simple(model_id, rag_system_prompt, prompt)
    
    return answer
