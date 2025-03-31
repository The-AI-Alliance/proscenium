from rich import print

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.read import load_file
from proscenium.verbs.chunk import documents_to_chunks_by_characters
from proscenium.verbs.vector_database import create_collection
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.display.milvus import collection_panel


def build_vector_db(
    data_file: str,
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str,
):

    documents = load_file(data_file)
    chunks = documents_to_chunks_by_characters(documents)
    print("Data file", data_file, "has", len(chunks), "chunks")

    create_collection(vector_db_client, embedding_fn, collection_name, overwrite=True)

    info = add_chunks_to_vector_db(
        vector_db_client, embedding_fn, chunks, collection_name
    )
    print(info["insert_count"], "chunks inserted")
    print(collection_panel(vector_db_client, collection_name))
