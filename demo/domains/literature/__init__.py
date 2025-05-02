from typing import Callable
from typing import List
from typing import Optional

import logging
from rich.console import Console

from .docs import books
from .chunk_space_builder import make_chunk_space_builder
from .chunk_space import default_collection_name, default_embedding_model_id
from .query_handler import user_prompt, default_question
from .query_handler import make_handler
from .query_handler import default_generator_model_id

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


def prerequisites(
    milvus_uri, collection_name, embedding_model_id, console: Optional[Console] = None
) -> List[Callable[[bool], None]]:

    build = make_chunk_space_builder(
        milvus_uri,
        collection_name,
        embedding_model_id,
        console=console,
    )

    return [build]
