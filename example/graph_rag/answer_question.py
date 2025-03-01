
from rich import print

question = "How has Judge Kenison used Ballou v. Ballou to rule on cases?"

##################################
# Connect to vector db
##################################

from .config import embedding_model_id, milvus_db_file
from proscenium.vector_database import vector_db

embedding_fn = embedding_function(embedding_model_id)
print("Embedding model", embedding_model_id)

vector_db_client = vector_db(milvus_db_file, embedding_fn)
print("Connected to vector db stored in", milvus_db_file)

##################################
# Extract entities from question
##################################

from .config import model_id, categories
from proscenium.complete import complete_simple
from proscenium.parse import extraction_template
from proscenium.parse import get_triples_from_extract

categories_str = "\n".join([f"{k}: {v}" for k, v in categories.items()])

response = complete_simple(model_id, "You are an entity extractor", extraction_template.format(
    categories = categories_str,
    text = question))
print(response)

question_entity_triples = get_triples_from_extract(response, "", categories)
print(question_entity_triples)

##################################
# Match entities to graph
##################################

from proscenium.vector_database import closest_chunks
from proscenium.vector_database import embedding_function
from proscenium.display import display_chunk_hits

def match_entity(name, threshold=1.0):

    """Match entities by embedding vector distance given a similarity threshold."""

    hits = closest_chunks(vector_db_client, embedding_fn, name, k=5)
    display_chunk_hits(hits)

    if len(hits) > 0:
        # TODO confirm that 0th element is the closest match
        hit = hits[0]
        if hit['distance'] <= threshold:
            return hit['entity']['text']
    else:
        return None

for triple in question_entity_triples:
    name = triple[0]
    print(f"\nMatching {name}")
    match = match_entity(name)
    if match is not None:
        print(f"Match: {match}")

##################################
# Connect to Neo4j
##################################

from .config import neo4j_uri, neo4j_username, neo4j_password
from proscenium.know import knowledge_graph_client

driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)

##################################
# Query graph for cases
##################################

from stringcase import snakecase, lowercase

def query_for_cases(entity_name, role):
    with driver.session() as session:
        relationship = snakecase(lowercase(role.replace('/', '_')))
        query = f"MATCH (e:Entity {{name: '{entity_name}'}})-[:{relationship}]->(c:Case) RETURN c.name AS name"
        print(query)
        result = session.run(query)
        print("Cases:")
        for record in result:
            print(record["name"])

for triple in question_entity_triples:
    entity, role, case = triple
    entity_match = match_entity(entity)
    query_for_cases(entity_match, role)

##################################
# Query for cases given multiple entities and their relationships to the case.
##################################

def query_for_cases(entity_role_pairs):
    with driver.session() as session:
        query = ""
        for i, (entity, role) in enumerate(entity_role_pairs):
            relationship = snakecase(lowercase(role.replace('/', '_')))
            query += f"MATCH (e{str(i)}:Entity {{name: '{entity}'}})-[:{relationship}]->(c)\n"
        query += "RETURN c.name AS name"
        print(query)
        result = session.run(query)
        cases = []
        print("Cases:")
        for record in result:
            cases.append(record["name"])
            print(record["name"])
        return cases

entity_role_pairs = []
for triple in question_entity_triples:
    entity, role, case = triple
    entity_match = match_entity(entity)
    entity_role_pairs.append((entity_match, role))
    
cases = query_for_cases(entity_role_pairs)

##################################
# Retrieve case text
##################################

# TODO avoid this by indexing the case text elsewhere (eg the graph)

from .config import hf_dataset_id, hf_dataset_column, num_docs
from proscenium.load import load_hugging_face_dataset

documents = load_hugging_face_dataset(hf_dataset_id, page_content_column=hf_dataset_column)
print("Document Count: " + str(len(documents)))

print("Truncating to ", num_docs)
documents = documents[:num_docs]

case_text = [doc.page_content for doc in documents if doc.metadata["name_abbreviation"] == cases[0]][0]
print(case_text)

##################################
# Answer question
##################################

query_template = """
Answer the question using the following text from one case: \n\n{case_text}

Question: {question}
"""

query = query_template.format(
    case_text = case_text,
    question = question)
print(query)

response = complete_simple(model_id, "You are a helpful law librarian", query)
print(response)
