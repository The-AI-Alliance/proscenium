
import tempfile

from .chunk import documents_to_chunks
from .prompts import rag_prompt_template

from langchain_core.vectorstores.base import VectorStore
from langchain_milvus import Milvus
from langchain_huggingface import HuggingFaceEmbeddings

def create_vector_db(embedding_model_id: str) -> tuple[Milvus, str]:

    embedding_model = HuggingFaceEmbeddings(model_name=embedding_model_id)

    db_file = tempfile.NamedTemporaryFile(prefix="milvus_", suffix=".db", delete=False).name

    vector_db = Milvus(
        embedding_function=embedding_model,
        connection_args={"uri": db_file},
        auto_id=True,
        index_params={"index_type": "AUTOINDEX"},
    )

    return vector_db, db_file


def add_chunked_file_to_vector_db(vector_db: VectorStore, filename: str) -> str:

    chunks = documents_to_chunks(filename)

    vector_db.add_documents(chunks)

    return filename, len(chunks)


def rag_prompt(vector_db: VectorStore, query: str) -> str:

    docs = vector_db.similarity_search(query)

    context = "\n\n".join([f"{i}. {doc.page_content}" for i, doc in enumerate(docs[:4])])

    return rag_prompt_template.format(context=context, query=query)
