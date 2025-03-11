
from pathlib import Path

milvus_uri = "file:/milvus.db"
#milvus_uri = "http://localhost:19530"

embedding_model_id = "all-MiniLM-L6-v2"

model_id = "ollama:llama3.2"
#model_id = "ollama:granite3.1-dense:2b"
#model_id = "openai:gpt-4o"

url = 'https://www.gutenberg.org/cache/epub/8714/pg8714.txt'
data_file = Path("four_plays_of_aeschylus.txt")
