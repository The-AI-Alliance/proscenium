from pathlib import Path

from demo.config import default_model_id

model_id = default_model_id

embedding_model_id = "all-MiniLM-L6-v2"


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
