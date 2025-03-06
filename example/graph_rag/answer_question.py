
import logging
from rich import print
from rich.table import Table

from proscenium.parse import get_triples_from_extract
from proscenium.complete import complete_simple
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.vector_database import embedding_function
from proscenium.know import knowledge_graph_client

import example.graph_rag.util as util
import example.graph_rag.config as config

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

embedding_fn = embedding_function(config.embedding_model_id)
print("Embedding model", config.embedding_model_id)

vector_db_client = vector_db(config.milvus_db_file, embedding_fn)
print("Connected to vector db stored in", config.milvus_db_file)

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

extract = complete_simple(
    config.model_id,
    util.extraction_system_prompt,
    util.extraction_template.format(text = config.question))

question_entity_triples = get_triples_from_extract(extract, "", config.predicates)
table = Table(title="Query Triples", show_lines=False)
table.add_column("Subject", justify="left", style="blue")
table.add_column("Predicate", justify="left", style="green")
table.add_column("Object", justify="left", style="red")
for triple in question_entity_triples:
    table.add_row(*triple)
print(table)

import sys
sys.exit(0)

entity_role_pairs = []
for triple in question_entity_triples:
    entity, role, case = triple
    entity_match = util.match_entity(entity)
    entity_role_pairs.append((entity_match, role))

cases = util.query_for_cases(driver, entity_role_pairs)

case_text = util.case_text_for_name(cases[0])
print(case_text)

query = util.graphrag_prompt(case_text, config.question)
print(query)

response = complete_simple(config.model_id, "You are a helpful law librarian", query)
print(response)
