
from typing import List

from pathlib import Path
from rich.panel import Panel
from rich.prompt import Prompt
from stringcase import snakecase, lowercase
from langchain_core.documents.base import Document

from proscenium.typer.config import default_model_id
from proscenium.verbs.parse import PartialFormatter
from proscenium.verbs.parse import raw_extraction_template

hf_dataset_id = "free-law/nh"
hf_dataset_column = "text"
num_docs = 4
# initial version looked at only: doc.metadata["id"] in ['4440632', '4441078']

#model_id = "openai:gpt-4o"
#model_id = "ollama:granite3.2"
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

def doc_as_rich(doc: Document):
    
    case_str = case_template.format_map(doc.metadata)

    return Panel(case_str, title=doc.metadata['name_abbreviation'])

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

partial_formatter = PartialFormatter()

extraction_template = partial_formatter.format(
    raw_extraction_template,
    predicates = "\n".join([f"{k}: {v}" for k, v in predicates.items()]))

entity_csv_file = Path("entities.csv")

neo4j_uri = "bolt://localhost:7687" # os.environ["NEO4J_URI"]
neo4j_username = "neo4j" # os.environ["NEO4J_USERNAME"]
neo4j_password = "password" # os.environ["NEO4J_PASSWORD"]

def add_triple(tx, entity: str, role: str, case: str) -> None:
    query = (
        "MERGE (e:Entity {name: $entity}) "
        "MERGE (c:Case {name: $case}) "
        "MERGE (e)-[r:%s]->(c)"
    ) % snakecase(lowercase(role.replace('/', '_')))
    tx.run(query, entity=entity, case=case)

embedding_model_id = "all-MiniLM-L6-v2"

milvus_uri = "file:/grag-milvus.db"

def matching_objects_query(
    subject_predicate_constraints: List[tuple[str, str]]) -> str:
    query = ""
    for i, (subject, predicate) in enumerate(subject_predicate_constraints):
        predicate_lc = snakecase(lowercase(predicate.replace('/', '_')))
        query += f"MATCH (e{str(i)}:Entity {{name: '{subject}'}})-[:{predicate_lc}]->(c)\n"
    query += "RETURN c.name AS name"

    return query

system_prompt = "You are a helpful law librarian"

graphrag_prompt_template = """
Answer the question using the following text from one case:

{document_text}

Question: {question}
"""

def get_user_question() -> str:

    question = Prompt.ask(
        f"What is your question about {hf_dataset_id}?",
        default = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"
        )

    return question
