from pathlib import Path

hf_dataset_id = "free-law/nh"
hf_dataset_column = "text"
num_docs = 4
# initial version looked at only: doc.metadata["id"] in ['4440632', '4441078']

model_id = "openai:gpt-4o"

entity_csv_file = Path("entities.csv")

neo4j_uri = "bolt://localhost:7687" # os.environ["NEO4J_URI"]
neo4j_username = "neo4j" # os.environ["NEO4J_USERNAME"]
neo4j_password = "password" # os.environ["NEO4J_PASSWORD"]

embedding_model_id = "all-MiniLM-L6-v2"
milvus_db_file = Path("milvus.db")

categories = {
    "Judge/Justice": "The name of the judge or justice involved in the case, including their role (e.g., trial judge, appellate judge, presiding justice).",
    "Precedent Cited": "Previous case law referred to in the case.",
}
