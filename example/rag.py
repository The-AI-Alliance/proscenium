
import os
import wget
from pymilvus import model
from proscenium.vector_database import create_vector_db
from proscenium.load import load_file
from proscenium.chunk import documents_to_chunks_by_characters
from proscenium.vector_database import add_chunks_to_vector_db
from proscenium.vector_database import rag_prompt
from proscenium.prompts import rag_system_prompt
from proscenium.inference import complete_simple

query = "What did Hermes say to Prometheus about giving fire to humans?"

data_file = "four_plays_of_aeschylus.txt"
if not os.path.exists(data_file):
    url = 'https://www.gutenberg.org/cache/epub/8714/pg8714.txt'
    wget.download(url, out=data_file)

embedding_fn = model.dense.SentenceTransformerEmbeddingFunction(
    model_name =  "all-MiniLM-L6-v2",
    device = 'cpu' # 'cpu' or 'cuda:0'
)

vector_db_client, db_file_name = create_vector_db(embedding_fn) 
print("DB file:", db_file_name)

documents = load_file(data_file)
chunks = documents_to_chunks_by_characters(documents)
print(f"Data file {data_file} has {len(chunks)} chunks")

info = add_chunks_to_vector_db(vector_db_client, embedding_fn, chunks)
print("Chunks inserted", info['insert_count'])

print("Query:", query)
prompt = rag_prompt(vector_db_client, embedding_fn, query)

#model_id = "ollama:llama3.2"
model_id = "ollama:granite3.1-dense:2b"
answer = complete_simple(model_id, rag_system_prompt, prompt)
print("Answer:", answer)
