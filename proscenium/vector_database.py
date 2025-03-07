
from typing import Dict, List

from pathlib import Path
from langchain_core.documents.base import Document
from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema
from pymilvus import model

# See https://milvus.io/docs/quickstart.md

def embedding_function(
    embedding_model_id: str) -> model.dense.SentenceTransformerEmbeddingFunction:
    embedding_fn = model.dense.SentenceTransformerEmbeddingFunction(
        model_name = embedding_model_id,
        device = 'cpu' # or 'cuda:0'
    )
    return embedding_fn

collection_name = "chunks"

def schema_chunks(embedding_fn: model.dense.SentenceTransformerEmbeddingFunction) -> CollectionSchema:

    field_id = FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True)
    field_text = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length= 50000)
    field_vector = FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim = embedding_fn.dim)

    schema = CollectionSchema(
        fields=[field_id, field_text, field_vector],
        description="Chunks Schema",
        enable_dynamic_field=True
    )

    return schema

def create_vector_db(
    db_file_name: Path,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    overwrite: bool = False
    ) -> MilvusClient:

    if db_file_name.exists():
        if overwrite:
            db_file_name.unlink()
            print("Deleted existing vector db file", db_file_name)
        else:
            print("File", db_file_name, "exists. Use overwrite=True to replace.")
            return None

    client = MilvusClient(str(db_file_name))

    client.create_collection(
        collection_name = collection_name,
        schema = schema_chunks(embedding_fn),
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

    return client


def vector_db(
    db_file_name: Path,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction
    ) -> MilvusClient:

    client = MilvusClient(str(db_file_name))

    client.load_collection(collection_name)

    return client


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
    k: int = 4) -> List[Dict]:

    result = client.search(
        collection_name = collection_name,
        data = embedding_fn.encode_queries([query]),
        anns_field = "vector",
        search_params = {"metric":"IP", "offset":0},
        output_fields = ["text"],
        limit = k)

    hits = result[0]

    return hits

#def rag_prompt(
#    chunks: List[Dict],
#    query: str) -> str:
#
#    context = "\n\n".join([f"CHUNK {chunk['id']}. {chunk['entity']['text']}" for i, chunk in enumerate(chunks)])
#
#    return rag_prompt_template.format(context=context, query=query)
