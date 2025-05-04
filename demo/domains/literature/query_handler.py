from typing import Generator
from typing import Callable

import logging

from rich.console import Console

from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db
from proscenium.scripts.rag import answer_question

from demo.config import default_model_id

from .docs import books
from .chunk_space import default_collection_name

log = logging.getLogger(__name__)

default_generator_model_id = default_model_id

user_prompt = f"What is your question about {', '.join([b.title for b in books])}?"

default_question = "What did Hermes say to Prometheus about giving fire to humans?"


def make_handler(
    generator_model_id: str,
    milvus_uri: str,
    embedding_model_id: str,
    admin_channel_id: str,
) -> Callable[[tuple[str, str, str]], Generator[tuple[str, str], None, None]]:

    vector_db_client = vector_db(milvus_uri)
    log.info("Vector db at uri %s", milvus_uri)

    embedding_fn = embedding_function(embedding_model_id)
    log.info("Embedding model %s", embedding_model_id)

    def handle(
        channel_id: str, speaker_id: str, question: str
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, answer_question(
            question,
            generator_model_id,
            vector_db_client,
            embedding_fn,
            default_collection_name,
        )

    return handle
