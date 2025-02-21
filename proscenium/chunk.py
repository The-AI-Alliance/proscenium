
from typing import List
import logging
import os

from langchain_core.documents.base import Document
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("langchain_text_splitters.base").setLevel(logging.ERROR)

def documents_to_chunks(
    filename: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 0) -> List[Document]:

    loader = TextLoader(filename)
    documents = loader.load()

    text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    return text_splitter.split_documents(documents)
