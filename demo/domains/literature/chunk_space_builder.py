from typing import Optional
from typing import Callable

import logging

import asyncio

from rich.console import Console

from proscenium.verbs.read import url_to_file
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.chunk_space import make_vector_db_builder

from .docs import books

log = logging.getLogger(__name__)


def make_chunk_space_builder(
    milvus_uri: str,
    collection_name: str,
    embedding_model_id: str,
    console: Optional[Console] = None,
) -> Callable[[bool], None]:

    def build(force: bool = False) -> None:

        if not force:
            vector_db_client = vector_db(milvus_uri, overwrite=False)
            if vector_db_client.has_collection(collection_name):
                # TODO the existence of the collection might not be strong enough proof
                log.info(
                    "Milvus DB already exists at %s with collection %s. Skipping its build.",
                    milvus_uri,
                    collection_name,
                )
                vector_db_client.close()
                return
            vector_db_client.close()

        for book in books:
            asyncio.run(url_to_file(book.url, book.data_file))
            log.info("%s local copy to chunk at %s", book.title, book.data_file)

        embedding_fn = embedding_function(embedding_model_id)
        log.info("Embedding model %s", embedding_model_id)

        vector_db_client = vector_db(milvus_uri, overwrite=True)
        log.info("Vector db at uri %s", milvus_uri)

        vector_db_build = make_vector_db_builder(
            [str(book.data_file) for book in books],
            vector_db_client,
            embedding_fn,
            collection_name,
        )

        log.info("Building chunk space")
        vector_db_build()

        vector_db_client.close()

    return build
