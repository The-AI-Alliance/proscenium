from typing import Optional

import logging

import asyncio

from rich.console import Console

from proscenium.core import Prop
from proscenium.verbs.read import url_to_file
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db

from proscenium.patterns.chunk_space import load_chunks

from .docs import books

log = logging.getLogger(__name__)

default_embedding_model_id = "all-MiniLM-L6-v2"

default_collection_name = "literature_chunks"


class ChunkSpace(Prop):
    """Small chunks of literature text stored in a vector database."""

    def __init__(
        self,
        milvus_uri: str,
        collection_name: str,
        embedding_model_id: str,
        console: Optional[Console] = None,
    ) -> None:
        super().__init__(console=console)
        self.milvus_uri = milvus_uri
        self.collection_name = collection_name
        self.embedding_model_id = embedding_model_id

    def already_built(self) -> bool:

        vector_db_client = vector_db(self.milvus_uri, overwrite=False)
        if vector_db_client.has_collection(self.collection_name):
            log.info(
                "Milvus DB already exists at %s with collection %s. Skipping its build.",
                self.milvus_uri,
                self.collection_name,
            )
            vector_db_client.close()
            return True
        vector_db_client.close()
        return False

    def build(self) -> None:

        for book in books:
            asyncio.run(url_to_file(book.url, book.data_file))
            log.info("%s local copy to chunk at %s", book.title, book.data_file)

        embedding_fn = embedding_function(self.embedding_model_id)
        log.info("Embedding model %s", self.embedding_model_id)

        vector_db_client = vector_db(self.milvus_uri, overwrite=True)
        log.info("Vector db at uri %s", self.milvus_uri)

        log.info("Building chunk space")
        load_chunks(
            [str(book.data_file) for book in books],
            vector_db_client,
            embedding_fn,
            self.collection_name,
        )

        vector_db_client.close()
