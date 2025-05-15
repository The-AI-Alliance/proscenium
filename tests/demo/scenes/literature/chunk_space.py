from typing import Optional
import logging
import asyncio
from rich.console import Console

from lapidarist.verbs.read import url_to_file
from lapidarist.verbs.vector_database import embedding_function
from lapidarist.verbs.vector_database import vector_db
from lapidarist.patterns.chunk_space import load_chunks_from_files

from proscenium.core import Prop

from .docs import books

log = logging.getLogger(__name__)


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

        vector_db_client = vector_db(self.milvus_uri)
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

        log.info("Building chunk space")
        load_chunks_from_files(
            [str(book.data_file) for book in books],
            self.milvus_uri,
            embedding_fn,
            self.collection_name,
            console=self.console,
        )
