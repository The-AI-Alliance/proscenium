from typing import Dict, List

import logging
from pathlib import Path
from langchain_core.documents.base import Document
from urllib.parse import urlsplit
from pymilvus import MilvusClient
from pymilvus import DataType, FieldSchema, CollectionSchema
from pymilvus import model

# See https://milvus.io/docs/quickstart.md

log = logging.getLogger(__name__)


def embedding_function(
    embedding_model_id: str,
) -> model.dense.SentenceTransformerEmbeddingFunction:
    embedding_fn = model.dense.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model_id, device="cpu"  # or 'cuda:0'
    )
    return embedding_fn


def schema_chunks(
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
) -> CollectionSchema:

    field_id = FieldSchema(
        name="id", dtype=DataType.INT64, is_primary=True, auto_id=True
    )
    field_text = FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=50000)
    field_vector = FieldSchema(
        name="vector", dtype=DataType.FLOAT_VECTOR, dim=embedding_fn.dim
    )

    schema = CollectionSchema(
        fields=[field_id, field_text, field_vector],
        description="Chunks Schema",
        enable_dynamic_field=True,
    )

    return schema


def vector_db(
    uri: str,
) -> MilvusClient:

    log.info("Connecting to vector db %s", uri)
    uri_fields = urlsplit(uri)
    client = None
    if uri_fields[0] == "file":
        file_path = Path(uri_fields[2][1:])
        if file_path.exists():
            log.info(
                "Using existing %s file.",
                uri_fields[2],
            )
        else:
            log.info("Creating new vector db file %s", file_path)

        client = MilvusClient(uri=str(file_path))

    else:

        log.info("Connecting to vector db at non-file uri %s", uri)
        client = MilvusClient(uri=uri)

    return client


def create_collection(
    client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str,
) -> None:

    client.create_collection(
        collection_name=collection_name,
        schema=schema_chunks(embedding_fn),
    )

    index_params = client.prepare_index_params()

    index_params.add_index(
        field_name="vector",
        index_type="IVF_FLAT",
        metric_type="IP",
        params={"nlist": 1024},
    )

    client.create_index(
        collection_name=collection_name, index_params=index_params, sync=True
    )
    log.info("Created collection %s", collection_name)


def add_chunks_to_vector_db(
    client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    chunks: List[Document],
    collection_name: str,
) -> Dict:

    vectors = embedding_fn.encode_documents([chunk.page_content for chunk in chunks])

    data = [
        {"text": chunk.page_content, "vector": vector}
        for chunk, vector in zip(chunks, vectors)
    ]

    insert_result = client.insert(collection_name, data)

    return insert_result


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
