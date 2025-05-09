from typing import Optional
import logging
from rich.console import Console
from pymilvus import model

from proscenium.verbs.read import load_file
from proscenium.verbs.chunk import documents_to_chunks_by_characters
from proscenium.verbs.display.milvus import collection_panel
from proscenium.verbs.vector_database import vector_db
from proscenium.verbs.vector_database import create_collection
from proscenium.verbs.vector_database import add_chunks_to_vector_db

log = logging.getLogger(__name__)


def load_chunks_from_files(
    data_files: list[str],
    milvus_uri: str,
    embedding_fn: model.dense.SentenceTransformerEmbeddingFunction,
    collection_name: str,
    console: Optional[Console] = None,
) -> None:

    vector_db_client = vector_db(milvus_uri)
    log.info("Vector db stored at %s", milvus_uri)

    for data_file in data_files:

        log.info(
            "Loading data file %s into vector db %s collection %s",
            data_file,
            milvus_uri,
            collection_name,
        )
        create_collection(vector_db_client, embedding_fn, collection_name)

        documents = load_file(data_file)
        chunks = documents_to_chunks_by_characters(documents)
        log.info("Data file %s has %s chunks", data_file, len(chunks))

        info = add_chunks_to_vector_db(
            vector_db_client,
            embedding_fn,
            chunks,
            collection_name,
        )
        log.info("%s chunks inserted ", info["insert_count"])
        if console is not None:
            console.print(collection_panel(vector_db_client, collection_name))

    vector_db_client.close()
