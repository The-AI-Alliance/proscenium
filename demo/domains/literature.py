from typing import Generator
from typing import Callable

from pathlib import Path

from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.rag import answer_question

from demo.config import default_model_id

default_generator_model_id = default_model_id

default_embedding_model_id = "all-MiniLM-L6-v2"


class Book:

    def __init__(self, title: str, url: str, data_file: Path):
        self.title = title
        self.url = url
        self.data_file = data_file


aeschylus = Book(
    title="The Four Plays of Aeschylus",
    url="https://www.gutenberg.org/cache/epub/8714/pg8714.txt",
    data_file=Path("four_plays_of_aeschylus.txt"),
)

walden = Book(
    title="Walden",
    url="https://www.gutenberg.org/cache/epub/205/pg205.txt",
    data_file=Path("walden.txt"),
)

books = [aeschylus, walden]

user_prompt = f"What is your question about {', '.join([b.title for b in books])}?"

default_question = "What did Hermes say to Prometheus about giving fire to humans?"


def make_handler(
    generator_model_id: str,
    milvus_uri: str,
    embedding_model_id: str,
    verbose: bool = False,
) -> Callable[[str], Generator[str, None, None]]:

    collection_name = "literature_chunks"

    vector_db_client = vector_db(milvus_uri)
    print("Vector db at uri", milvus_uri)

    embedding_fn = embedding_function(embedding_model_id)
    print("Embedding model:", embedding_model_id)

    def handle(question: str) -> Generator[str, None, None]:

        yield answer_question(
            question,
            generator_model_id,
            vector_db_client,
            embedding_fn,
            collection_name,
            verbose,
        )

    return handle
