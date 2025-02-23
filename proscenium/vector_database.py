
from typing import Dict, List

from .prompts import rag_prompt_template

from pathlib import Path
from langchain_core.documents.base import Document
from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema
# from milvus_model.base import BaseEmbeddingFunction
from pymilvus import model

# See https://milvus.io/docs/quickstart.md

collection_name = "chunks"

def create_vector_db(
    db_file_name: Path,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction
    ) -> tuple[MilvusClient, str]:

    client = MilvusClient(db_file_name)

    field_id = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
    field_text = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length= 50000)
    field_vector = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim = embedding_fn.dim)

    schema_chunks = CollectionSchema(
        fields=[field_id, field_text, field_vector],
        description="Chunks Schema",
        enable_dynamic_field=True
    )

    client.create_collection(
        collection_name = collection_name,
        schema = schema_chunks,
    )

    index_params = client.prepare_index_params()

    index_params.add_index(
        field_name="vector", 
        index_type="IVF_FLAT",
        metric_type="IP",
        params={"nlist": 1024}
    )

    client.create_index(
        collection_name = collection_name,
        index_params = index_params,
        sync = False
    )

    return client, db_file_name


def add_chunks_to_vector_db(
        client: MilvusClient,
        embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
        chunks: List[Document]) -> Dict:

    vectors = embedding_fn.encode_documents([chunk.page_content for chunk in chunks])

    data = [{"text": chunk.page_content, "vector": vector} for chunk, vector in zip(chunks, vectors)]

    insert_result = client.insert(collection_name, data) 

    return insert_result

def closest_chunks(
    client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    query: str,
    k: int = 4) -> List[str]:

    chunks = client.search(
        collection_name = collection_name,
        data = embedding_fn.encode_queries([query]),
        anns_field = "vector",
        search_params = {"metric":"IP", "offset":0},
        output_fields = ["text"],
        limit = k)

    return chunks


def rag_prompt(
    chunks: List[str],
    query: str) -> str:

    context = "\n\n".join([f"{i}. {chunk}" for i, chunk in enumerate(chunks)])

    return rag_prompt_template.format(context=context, query=query)
