
import asyncio
from pathlib import Path
from pymilvus import model
from pydantic.networks import HttpUrl
from proscenium.web import url_to_file
from proscenium.vector_database import create_vector_db
from proscenium.load import load_file
from proscenium.chunk import documents_to_chunks_by_characters
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import rag_prompt
from proscenium.prompts import rag_system_prompt
from proscenium.inference import complete_simple

from rich import print

print("[bold]Proscenium[/bold]", ":performing_arts:")
print("[bold]The AI Alliance[/bold]")
print()

data_file = Path("four_plays_of_aeschylus.txt")
if not data_file.exists():
    url = HttpUrl('https://www.gutenberg.org/cache/epub/8714/pg8714.txt')
    print("downloading", url)
    asyncio.run(url_to_file(url, data_file))
print("Data files to chunk:", data_file)

embedding_model_id = "all-MiniLM-L6-v2"
embedding_fn = model.dense.SentenceTransformerEmbeddingFunction(
    model_name = embedding_model_id,
    device = 'cpu' # 'cpu' or 'cuda:0'
)
print("Embedding model", embedding_model_id)

vector_db_client, db_file_name = create_vector_db(embedding_fn) 
print("Vector db stored in temp file", db_file_name)

documents = load_file(data_file)
chunks = documents_to_chunks_by_characters(documents)
print("Data file", data_file, "has", len(chunks), "chunks")

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
print(info['insert_count'], "chunks inserted")

query = "What did Hermes say to Prometheus about giving fire to humans?"

print("USER")
print(query)
prompt = rag_prompt(vector_db_client, embedding_fn, query)

#model_id = "ollama:llama3.2"
model_id = "ollama:granite3.1-dense:2b"
answer = complete_simple(model_id, rag_system_prompt, prompt)
print("ASSISTANT")
print(answer)
