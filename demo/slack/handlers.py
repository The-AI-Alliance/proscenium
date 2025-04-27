from typing import Optional
from pathlib import Path
import os

from proscenium.verbs.complete import complete_simple
from proscenium.verbs.know import knowledge_graph_client
from proscenium.scripts.graph_rag import query_to_prompts

default_enrichment_jsonl_file = Path("enrichments.jsonl")
default_neo4j_uri = "bolt://localhost:7687"
default_neo4j_username = "neo4j"
default_neo4j_password = "password"
default_milvus_uri = "file:/grag-milvus.db"

neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)
milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

driver = knowledge_graph_client(neo4j_uri, neo4j_username, neo4j_password)


def handle_abacus(question: str, verbose: bool = False) -> Optional[str]:

    from proscenium.verbs.invoke import process_tools
    from proscenium.scripts.tools import apply_tools

    import demo.domains.abacus as domain

    from demo.config import default_model_id

    answer = apply_tools(
        model_id=default_model_id,
        system_message=domain.system_message,
        message=question,
        tool_desc_list=domain.tool_desc_list,
        tool_map=domain.tool_map,
        rich_output=verbose,
    )

    return answer


def handle_literature(question: str, verbose: bool = False) -> Optional[str]:

    from proscenium.verbs.vector_database import embedding_function
    from proscenium.verbs.vector_database import vector_db

    from proscenium.scripts.rag import answer_question
    from proscenium.scripts.chunk_space import build_vector_db as bvd
    import demo.domains.literature as domain

    milvus_uri = os.environ.get("MILVUS_URI", default_milvus_uri)

    collection_name = "literature_chunks"

    vector_db_client = vector_db(milvus_uri)
    print("Vector db at uri", milvus_uri)

    embedding_fn = embedding_function(domain.embedding_model_id)
    print("Embedding model:", domain.embedding_model_id)

    answer = answer_question(
        question,
        domain.model_id,
        vector_db_client,
        embedding_fn,
        collection_name,
        verbose,
    )

    return answer


def handle_legal(question: str, verbose: bool = False) -> Optional[str]:

    import demo.domains.legal as domain

    prompts = query_to_prompts(
        question,
        domain.default_query_extraction_model_id,
        milvus_uri,
        driver,
        domain.query_extract,
        domain.query_extract_to_graph,
        domain.query_extract_to_context,
        domain.context_to_prompts,
        verbose,
    )

    if prompts is None:

        print("Unable to form prompts")
        return None

    else:

        system_prompt, user_prompt = prompts

        response = complete_simple(
            domain.default_generation_model_id,
            system_prompt,
            user_prompt,
            rich_output=verbose,
        )

        return response


channel_to_handler = {
    "legal": handle_legal,
    "abacus": handle_abacus,
    "literature": handle_literature,
}


def stop_handlers():
    # TODO call stop on all handlers
    driver.close()
