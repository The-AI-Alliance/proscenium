

hf_dataset_id = "free-law/nh"
hf_dataset_column = "text"
num_docs = 10

model_id = "openai:gpt-4o"

embedding_model_id = "all-MiniLM-L6-v2"
milvus_db_file = "milvus.db"

categories = {
    "Judge/Justice": "The name of the judge or justice involved in the case, including their role (e.g., trial judge, appellate judge, presiding justice).",
    "Precedent Cited": "Previous case law referred to in the case.",
}
