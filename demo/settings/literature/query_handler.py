from typing import Generator

import logging

from proscenium.core import Character
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db
from proscenium.patterns.rag import answer_question

from demo.config import default_model_id

from .docs import books
from .chunk_space import default_collection_name

log = logging.getLogger(__name__)

default_generator_model_id = default_model_id

user_prompt = f"What is your question about {', '.join([b.title for b in books])}?"

default_question = "What did Hermes say to Prometheus about giving fire to humans?"


class LiteratureExpert(Character):

    def __init__(
        self,
        generator_model_id: str,
        milvus_uri: str,
        embedding_model_id: str,
        admin_channel_id: str,
    ):
        super().__init__(admin_channel_id=admin_channel_id)
        self.generator_model_id = generator_model_id
        self.milvus_uri = milvus_uri
        self.embedding_model_id = embedding_model_id

        self.vector_db_client = vector_db(self.milvus_uri)
        log.info("Vector db at uri %s", milvus_uri)

        self.embedding_fn = embedding_function(embedding_model_id)
        log.info("Embedding model %s", embedding_model_id)

    def handle(
        self, channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, answer_question(
            utterance,
            self.generator_model_id,
            self.vector_db_client,
            self.embedding_fn,
            default_collection_name,
        )
