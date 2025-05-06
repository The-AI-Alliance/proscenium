from typing import List
from typing import Optional
import logging
from rich.console import Console

from proscenium.core import Prop

from .docs import books
from .chunk_space import default_collection_name, default_embedding_model_id, ChunkSpace
from .query_handler import user_prompt, default_question
from .query_handler import default_generator_model_id

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


def props(
    milvus_uri, collection_name, embedding_model_id, console: Optional[Console] = None
) -> List[Prop]:

    chunk_space = ChunkSpace(
        milvus_uri,
        collection_name,
        embedding_model_id,
        console=console,
    )

    return [chunk_space]
