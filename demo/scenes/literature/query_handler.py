from typing import Generator

import logging
import json

from proscenium.core import Character
from proscenium.core import WantsToHandleResponse
from proscenium.core import control_flow_system_prompt
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db
from proscenium.patterns.rag import answer_question

from .docs import books

log = logging.getLogger(__name__)

user_prompt = f"What is your question about {', '.join([b.title for b in books])}?"

default_question = "What did Hermes say to Prometheus about giving fire to humans?"

wants_to_handle_template = """\
The text below is a user-posted message to a chat channel.
Determine if you, the AI assistant equipped with a vector database
with chunks from books: {book_titles},
might be able to find an answer to the user's question.
State a boolean value for whether you want to handle the message,
expressed in the specified JSON response format.
Only answer in JSON.

The user-posted message is:

{text}
"""


class LiteratureExpert(Character):
    """
    A literature expert character that can answer questions about literature."""

    def __init__(
        self,
        generator_model: str,
        control_flow_model: str,
        milvus_uri: str,
        embedding_model: str,
        collection_name: str,
        admin_channel_id: str,
    ):
        super().__init__(admin_channel_id=admin_channel_id)
        self.generator_model = generator_model
        self.control_flow_model = control_flow_model
        self.milvus_uri = milvus_uri
        self.embedding_model = embedding_model
        self.collection_name = collection_name

        self.vector_db_client = vector_db(self.milvus_uri)
        log.info("Vector db at uri %s", milvus_uri)

        self.embedding_fn = embedding_function(embedding_model)
        log.info("Embedding model %s", embedding_model)

    def wants_to_handle(self, channel_id: str, speaker_id: str, utterance: str) -> bool:

        log.info("handle? channel_id = %s, speaker_id = %s", channel_id, speaker_id)

        response = complete_simple(
            model_id=self.control_flow_model,
            system_prompt=control_flow_system_prompt,
            user_prompt=wants_to_handle_template.format(
                book_titles=", ".join([f'"{b.title}' for b in books]), text=utterance
            ),
            response_format={
                "type": "json_object",
                "schema": WantsToHandleResponse.model_json_schema(),
            },
        )

        try:
            response_json = json.loads(response)
            result_message = WantsToHandleResponse(**response_json)
            log.info("wants_to_handle: result = %s", result_message.wants_to_handle)
            return result_message.wants_to_handle

        except Exception as e:

            log.error("Exception: %s", e)

    def handle(
        self, channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, answer_question(
            utterance,
            self.generator_model,
            self.vector_db_client,
            self.embedding_fn,
            self.collection_name,
        )
