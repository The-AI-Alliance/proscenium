
from typing import Dict

import tempfile

from .chunk import documents_to_chunks
from .prompts import rag_prompt_template

from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema, Collection
# from milvus_model.base import BaseEmbeddingFunction
from pymilvus import model

#from sentence_transformers import SentenceTransformer

# See https://milvus.io/docs/quickstart.md

collection_name = "chunks"

def create_vector_db(
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction
    ) -> tuple[MilvusClient, str]:

    db_file_name = tempfile.NamedTemporaryFile(prefix="milvus_", suffix=".db", delete=False).name

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


def add_chunked_file_to_vector_db(
        client: MilvusClient,
        embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
        filename: str,
        first_id: int = 0) -> Dict:

    chunks = documents_to_chunks(filename)

    vectors = embedding_fn.encode_documents([chunk.page_content for chunk in chunks])
    # print("Dim:", embedding_fn.dim, vectors[0].shape)

    data = [{"text": chunks[i].page_content, "vector": vectors[i]} for i in range(len(vectors))]
    #print("Data has", len(data), "entities, each with fields: ", data[0].keys())
    #print("Vector dim:", len(data[0]["vector"]))

    insert_result = client.insert(collection_name, data) 

    return insert_result

def rag_prompt(
    client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    query: str,
    k: int = 4) -> str:

    chunks = client.search(
        collection_name = collection_name,
        data = embedding_fn.encode_queries([query]),
        anns_field = "vector",
        search_params = {"metric":"IP", "offset":0},
        output_fields = ["text"],
        limit = k)

    context = "\n\n".join([f"{i}. {chunk}" for i, chunk in enumerate(chunks)])

    return rag_prompt_template.format(context=context, query=query)
