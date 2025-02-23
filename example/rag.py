
import asyncio
from rich import print

print("[bold]Proscenium[/bold]", ":performing_arts:")
print("[bold]The AI Alliance[/bold]")
print()

from pathlib import Path
from pydantic.networks import HttpUrl
from proscenium.web import url_to_file
data_file = Path("four_plays_of_aeschylus.txt")
if not data_file.exists():
    url = HttpUrl('https://www.gutenberg.org/cache/epub/8714/pg8714.txt')
    print("downloading", url)
    asyncio.run(url_to_file(url, data_file))
print("Data files to chunk:", data_file)

from pymilvus import model
embedding_model_id = "all-MiniLM-L6-v2"
embedding_fn = model.dense.SentenceTransformerEmbeddingFunction(
    model_name = embedding_model_id,
    device = 'cpu' # 'cpu' or 'cuda:0'
)
print("Embedding model", embedding_model_id)

from proscenium.vector_database import create_vector_db

db_file_name = Path("milvus.db")
vector_db_client = create_vector_db(db_file_name, embedding_fn) 
print("Vector db stored in file", db_file_name)

from proscenium.load import load_file
from proscenium.chunk import documents_to_chunks_by_characters
documents = load_file(data_file)
chunks = documents_to_chunks_by_characters(documents)
print("Data file", data_file, "has", len(chunks), "chunks")

from proscenium.vector_database import add_chunks_to_vector_db
info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
print(info['insert_count'], "chunks inserted")

query = "What did Hermes say to Prometheus about giving fire to humans?"

from proscenium.vector_database import rag_prompt
print("USER")
print(query)
prompt = rag_prompt(vector_db_client, embedding_fn, query)

from proscenium.prompts import rag_system_prompt
from proscenium.inference import complete_simple
#model_id = "ollama:llama3.2"
model_id = "ollama:granite3.1-dense:2b"
answer = complete_simple(model_id, rag_system_prompt, prompt)
print("ASSISTANT")
print(answer)
