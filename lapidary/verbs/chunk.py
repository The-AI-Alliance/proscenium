import logging
import os
from typing import List
from typing import Iterable

from langchain_core.documents.base import Document

from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import TokenTextSplitter

log = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("langchain_text_splitters.base").setLevel(logging.ERROR)

# Each text chunk inherits the metadata from the document.


def documents_to_chunks_by_characters(
    documents: Iterable[Document], chunk_size: int = 1000, chunk_overlap: int = 0
) -> List[Document]:

    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    chunks = text_splitter.split_documents(documents)

    return chunks


def documents_to_chunks_by_tokens(
    documents: Iterable[Document], chunk_size: int = 1000, chunk_overlap: int = 0
) -> List[Document]:

    text_splitter = TokenTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    chunks = text_splitter.split_documents(documents)

    return chunks
