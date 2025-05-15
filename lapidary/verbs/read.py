from typing import List

import os
import logging

import httpx
from pydantic.networks import HttpUrl
from pathlib import Path

from langchain_core.documents.base import Document
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders.hugging_face_dataset import (
    HuggingFaceDatasetLoader,
)

log = logging.getLogger(__name__)

os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.getLogger("langchain_text_splitters.base").setLevel(logging.ERROR)


def load_file(filename: str) -> List[Document]:

    loader = TextLoader(filename)
    documents = loader.load()

    return documents


def load_hugging_face_dataset(
    dataset_name: str, page_content_column: str = "text"
) -> List[Document]:

    loader = HuggingFaceDatasetLoader(
        dataset_name, page_content_column=page_content_column
    )
    documents = loader.load()

    return documents


async def url_to_file(url: HttpUrl, data_file: Path, overwrite: bool = False):

    if data_file.exists() and not overwrite:
        return

    async with httpx.AsyncClient() as client:

        response = await client.get(url)
        response.raise_for_status()

        with open(data_file, "wb") as file:
            file.write(response.content)
