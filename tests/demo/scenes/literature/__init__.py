from typing import List
from typing import Optional
import logging
from rich.console import Console

from proscenium import Prop
from proscenium import Character
from proscenium import Scene

from .docs import books
from .chunk_space import ChunkSpace
from .query_handler import LiteratureExpert

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


class HighSchoolEnglishClass(Scene):
    """
    A high school English class where students can ask questions about
    literature and receive answers from a literature expert.
    """

    def __init__(
        self,
        channel_id_literature: str,
        milvus_uri: str,
        admin_channel_id: str,
        collection_name: str,
        embedding_model: str,
        generator_model: str,
        control_flow_model: str,
        console: Optional[Console] = None,
    ):
        super().__init__()

        self.channel_id_literature = channel_id_literature

        self.chunk_space = ChunkSpace(
            milvus_uri,
            collection_name,
            embedding_model,
            console=console,
        )

        self.literature_expert = LiteratureExpert(
            generator_model,
            control_flow_model,
            milvus_uri,
            embedding_model,
            collection_name,
            admin_channel_id,
        )

    def props(self) -> List[Prop]:

        return [self.chunk_space]

    def characters(self) -> List[Character]:

        return [self.literature_expert]

    def places(
        self,
        channel_name_to_id: dict,
    ) -> dict[str, Character]:

        return {channel_name_to_id[self.channel_id_literature]: self.literature_expert}
