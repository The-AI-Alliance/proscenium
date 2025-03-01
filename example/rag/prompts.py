
from typing import List, Dict

rag_system_prompt = "Use the following pieces of context to answer the question at the end. If you don't know the answer, just say that you don't know, don't try to make up an answer."

rag_prompt_template = """
The document chunks that are most similar to the query are:

{context}

Question:

{query}

Answer:
"""

def rag_prompt(
    chunks: List[Dict],
    query: str
) -> str:

    context = "\n\n".join([f"CHUNK {chunk['id']}. {chunk['entity']['text']}" for i, chunk in enumerate(chunks)])

    return rag_prompt_template.format(context=context, query=query)
