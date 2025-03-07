
import logging
import sys
from rich import print
from rich.panel import Panel

from proscenium.parse import get_triples_from_extract
from proscenium.complete import complete_simple
from proscenium.vector_database import embedding_function
from proscenium.vector_database import vector_db
from proscenium.vector_database import closest_chunks
from proscenium.know import knowledge_graph_client
from proscenium.display import print_header, display_triples, display_pairs

import example.graph_rag.util as util
import example.graph_rag.config as config

logging.basicConfig()
logging.getLogger().setLevel(logging.WARNING)

print_header()

print(Panel(config.question, title="Question"))

extraction_response = complete_simple(
    config.model_id,
    util.extraction_system_prompt,
    util.extraction_template.format(text = config.question),
    rich_output = True)

print("\nExtracting triples from extraction response")
question_entity_triples = get_triples_from_extract(extraction_response, "", config.predicates)
print("\n")
if len(question_entity_triples) == 0:
    print("No triples extracted from question")
    sys.exit(1)
display_triples(question_entity_triples, "Query Triples")

print("\nFinding entity matches for triples")
embedding_fn = embedding_function(config.embedding_model_id)
vector_db_client = vector_db(config.milvus_db_file, embedding_fn)
print("\n")
print("Connected to vector db stored in", config.milvus_db_file)
print("Embedding model", config.embedding_model_id)
print("\n")
subject_predicate_pairs = []
for triple in question_entity_triples:
    print("Finding entity matches for", triple[0], "(", triple[1], ")")
    subject, predicate, object = triple
    # TODO apply distance threshold
    hits = closest_chunks(vector_db_client, embedding_fn, subject, k=5)
    for match in [head['entity']['text'] for head in hits[:1]]:
        print("   match:", match)
        subject_predicate_pairs.append((match, predicate))
# Note: the above block loses the tie-back link from the match to the original triple
print("\n")
display_pairs(subject_predicate_pairs, "Subject Predicate Constraints")

driver = knowledge_graph_client(
    config.neo4j_uri,
    config.neo4j_username,
    config.neo4j_password)

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

else:

    print("No objects found for entity role pairs")
    sys.exit(1)
