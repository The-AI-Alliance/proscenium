from typing import List
from typing import Optional
import logging
from rich.console import Console

from proscenium.core import Prop
from proscenium.core import Character
from proscenium.core import Scene

from .chunk_space import default_collection_name, default_embedding_model_id, ChunkSpace
from .query_handler import default_generator_model_id
from .query_handler import LiteratureExpert

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


class HighSchoolEnglishClass(Scene):

    def __init__(
        self,
        milvus_uri,
        admin_channel_id: str,
        collection_name: str = default_collection_name,
        embedding_model_id: str = default_embedding_model_id,
        generator_model_id: str = default_generator_model_id,
        console: Optional[Console] = None,
    ):
        super().__init__()

        self.chunk_space = ChunkSpace(
            milvus_uri,
            collection_name,
            embedding_model_id,
            console=console,
        )

        self.literature_expert = LiteratureExpert(
            generator_model_id, milvus_uri, embedding_model_id, admin_channel_id
        )

    def props(self) -> List[Prop]:

        return [self.chunk_space]

    def characters(self) -> List[Character]:

        return [self.literature_expert]

    def places(
        self,
        channel_name_to_id: dict,
    ) -> dict[str, Character]:

        return {channel_name_to_id["literature"]: self.literature_expert}
