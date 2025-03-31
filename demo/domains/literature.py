from pathlib import Path

from demo.config import default_model_id

model_id = default_model_id

embedding_model_id = "all-MiniLM-L6-v2"

url = "https://www.gutenberg.org/cache/epub/8714/pg8714.txt"
data_file = Path("four_plays_of_aeschylus.txt")

user_prompt = "What is your question about The Four Plays of Aeschylus?"
default_question = "What did Hermes say to Prometheus about giving fire to humans?"
