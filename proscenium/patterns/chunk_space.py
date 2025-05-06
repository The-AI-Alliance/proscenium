import logging

from pymilvus import MilvusClient
from pymilvus import model

from proscenium.verbs.read import load_file
from proscenium.verbs.chunk import documents_to_chunks_by_characters
from proscenium.verbs.vector_database import create_collection
from proscenium.verbs.vector_database import add_chunks_to_vector_db
from proscenium.verbs.display.milvus import collection_panel

log = logging.getLogger(__name__)


def load_chunks(
    data_files: list[str],
    vector_db_client: MilvusClient,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str,
):
    create_collection(vector_db_client, embedding_fn, collection_name, overwrite=True)
    log.info("Created collection %s", collection_name)

    for data_file in data_files:

        log.info("Loading data file %s", data_file)

        documents = load_file(data_file)
        chunks = documents_to_chunks_by_characters(documents)
        log.info("Data file %s has %s chunks", data_file, len(chunks))

        info = add_chunks_to_vector_db(
            vector_db_client, embedding_fn, chunks, collection_name
        )
        log.info("%s chunks inserted", info["insert_count"])

    log.info(collection_panel(vector_db_client, collection_name))
