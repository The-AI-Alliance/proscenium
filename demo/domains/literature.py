from typing import Generator
from typing import Callable
from typing import List

import asyncio

from pathlib import Path

from proscenium.verbs.read import url_to_file
from proscenium.verbs.vector_database import embedding_function
from proscenium.verbs.vector_database import vector_db

from proscenium.scripts.chunk_space import make_vector_db_builder
from proscenium.scripts.rag import answer_question

from demo.config import default_model_id

default_generator_model_id = default_model_id

default_embedding_model_id = "all-MiniLM-L6-v2"

default_collection_name = "literature_chunks"


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


def make_chunk_space_builder(
    milvus_uri: str,
    collection_name: str,
    embedding_model_id: str,
    verbose: bool = False,
) -> Callable[[bool], None]:

    def build(force: bool = False) -> None:

        if not force:
            vector_db_client = vector_db(milvus_uri, overwrite=False)
            if vector_db_client.has_collection(collection_name):
                # TODO the existence of the collection might not be strong enough proof
                print(
                    f"Milvus DB already exists at {milvus_uri} with collection {collection_name}.",
                    "Skipping its build.",
                )
                vector_db_client.close()
                return
            vector_db_client.close()

        for book in books:
            if not Path(book.data_file).exists():
                asyncio.run(url_to_file(book.url, book.data_file))
            if verbose:
                print(book.title, "local copy to chunk at", book.data_file)

        embedding_fn = embedding_function(embedding_model_id)
        if verbose:
            print("Embedding model", embedding_model_id)

        vector_db_client = vector_db(milvus_uri, overwrite=True)
        if verbose:
            print("Vector db at uri", milvus_uri)

        vector_db_build = make_vector_db_builder(
            [str(book.data_file) for book in books],
            vector_db_client,
            embedding_fn,
            collection_name,
        )

        print("Building chunk space")
        vector_db_build()

        vector_db_client.close()

    return build


def prerequisites(
    milvus_uri, collection_name, embedding_model_id, verbose: bool = False
) -> List[Callable[[bool], None]]:

    build = make_chunk_space_builder(
        milvus_uri,
        collection_name,
        embedding_model_id,
        verbose=verbose,
    )

    return [build]


def make_handler(
    generator_model_id: str,
    milvus_uri: str,
    embedding_model_id: str,
    verbose: bool = False,
) -> Callable[[str], Generator[str, None, None]]:

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
            default_collection_name,
            verbose,
        )

    return handle
