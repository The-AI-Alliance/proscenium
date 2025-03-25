
from pathlib import Path
from rich.prompt import Prompt

from demo.typer.config import default_model_id

milvus_uri = "file:/milvus.db"
#milvus_uri = "http://localhost:19530"

embedding_model_id = "all-MiniLM-L6-v2"

model_id = default_model_id

url = 'https://www.gutenberg.org/cache/epub/8714/pg8714.txt'
data_file = Path("four_plays_of_aeschylus.txt")

def get_user_question() -> str:

    question = Prompt.ask(
        f"What is your question about The Four Plays of Aeschylus?",
        default = "What did Hermes say to Prometheus about giving fire to humans?"
        )

    return question
