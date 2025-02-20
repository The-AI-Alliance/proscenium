
import os
import wget
from proscenium.vector_database import create_vector_db
from proscenium.vector_database import add_chunked_file_to_vector_db
from proscenium.vector_database import rag_prompt
from proscenium.prompts import rag_system_prompt
from proscenium.inference import complete_simple

query = "What did Hermes say to Prometheus about giving fire to humans?"

data_file = "four_plays_of_aeschylus.txt"
if not os.path.exists(data_file):
    url = 'https://www.gutenberg.org/cache/epub/8714/pg8714.txt'
    wget.download(url, out=data_file)

embedding_model_id = "all-MiniLM-L6-v2"
vector_db, db_file = create_vector_db(embedding_model_id) 

num_chunks = add_chunked_file_to_vector_db(vector_db, data_file)

prompt = rag_prompt(vector_db, query)

model_id = "openai:gpt-4o"
answer = complete_simple(model_id, rag_system_prompt, prompt)
print(answer)
