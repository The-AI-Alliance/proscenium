
import logging
from rich import print
from rich.panel import Panel

from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.know import knowledge_graph_client
<<<<<<< HEAD
from proscenium.display import header
=======
from proscenium.display import header, triples_table, pairs_table
>>>>>>> main

import example.graph_rag.util as util
import example.graph_rag.config as config

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

print(header())

embedding_fn = embedding_function(config.embedding_model_id)
vector_db_client = vector_db(config.milvus_uri)
print("Connected to vector db stored at", config.milvus_uri, "with embedding model", config.embedding_model_id)
print("\n")

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

question = config.get_user_question()

answer = util.answer_question(
    question,
    config.hf_dataset_id,
    config.hf_dataset_column,
    config.num_docs,
    config.doc_as_object,
    config.model_id,
<<<<<<< HEAD
    config.extraction_template,
    config.system_prompt,
    config.graphrag_prompt_template,
    driver,
    vector_db_client,
    embedding_fn,
    config.matching_objects_query,
    config.predicates)
=======
    util.extraction_system_prompt,
    util.extraction_template.format(text = config.question),
    rich_output = True)

print("\nExtracting triples from extraction response")
question_entity_triples = get_triples_from_extract(extraction_response, "", config.predicates)
print("\n")
if len(question_entity_triples) == 0:
    print("No triples extracted from question")
    sys.exit(1)
print(triples_table(question_entity_triples, "Query Triples"))

print("Finding entity matches for triples")
subject_predicate_pairs = util.find_matching_objects(vector_db_client, embedding_fn, question_entity_triples)
print("\n")
pairs_table(subject_predicate_pairs, "Subject Predicate Constraints")

print("Querying for objects that match those constraints")
object_names = util.query_for_objects(driver, subject_predicate_pairs)
print("Objects with names:", object_names, "are matches for", subject_predicate_pairs)

if len(object_names) > 0:

    doc = util.full_doc_by_id(object_names[0])

    user_prompt = config.graphrag_prompt_template.format(
        case_text = doc.page_content,
        question = config.question)

    response = complete_simple(
        config.model_id,
        config.system_prompt,
        user_prompt,
        rich_output = True)

    print(Panel(response, title="Answer"))
>>>>>>> main

if answer:
    print(Panel(answer, title="Answer"))
else:
    print("No answer")

driver.close()
vector_db_client.close()
