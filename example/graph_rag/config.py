from pathlib import Path
from rich import print
from rich.panel import Panel
from langchain_core.documents.base import Document

hf_dataset_id = "free-law/nh"
hf_dataset_column = "text"
num_docs = 4
# initial version looked at only: doc.metadata["id"] in ['4440632', '4441078']

#model_id = "openai:gpt-4o"
#model_id = "ollama:granite3.1-dense:2b"
model_id = "ollama:llama3.2"

case_template = """
[u]{name}[/u]
{reporter}, Volume {volume} pages {first_page}-{last_page}
Court: {court}
Decision Date: {decision_date}
Citations: {citations}

Docket Number: {docket_number}
Jurisdiction: {jurisdiction}
Judges: {judges}
Parties: {parties}

Word Count: {word_count}, Character Count: {char_count}
Last Updated: {last_updated}, Provenance: {provenance}
Id: {id}
""" # leaves out head_matter

def doc_display(doc: Document):
    case_str = case_template.format_map(doc.metadata)
    print(Panel(case_str, title=doc.metadata['name_abbreviation']))
    print()

def doc_as_object(doc: Document) -> str:
    return doc.metadata['name_abbreviation']

def doc_direct_triples(doc: Document) -> list[tuple[str, str, str]]:
    object: str = doc_as_object(doc)
    return [(doc.metadata["court"], 'Court', object)]

# For the purpose of this recipe, note that the `judge`
# is not well captured in many of these documents;
# we will be extracting it from the case law text.

predicates = {
    "Judge/Justice": "The name of the judge or justice involved in the case, including their role (e.g., trial judge, appellate judge, presiding justice).",
    "Precedent Cited": "Previous case law referred to in the case.",
}

entity_csv_file = Path("entities.csv")

neo4j_uri = "bolt://localhost:7687" # os.environ["NEO4J_URI"]
neo4j_username = "neo4j" # os.environ["NEO4J_USERNAME"]
neo4j_password = "password" # os.environ["NEO4J_PASSWORD"]

embedding_model_id = "all-MiniLM-L6-v2"

milvus_uri = "file:/grag-milvus.db"

system_prompt = "You are a helpful law librarian"

graphrag_prompt_template = """
Answer the question using the following text from one case:

{document_text}

Question: {question}
"""

question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"
