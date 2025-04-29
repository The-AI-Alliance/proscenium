from pathlib import Path


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
