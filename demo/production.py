import logging
from pathlib import Path
import os

from rich.console import Console

from proscenium.core import Production
from proscenium.core import Character
from proscenium.core import Scene

from demo.scenes import abacus, literature, legal
from demo.scenes.legal.docs import default_docs_per_dataset

log = logging.getLogger(__name__)

literature_milvus_uri = "file:/milvus.db"

enrichment_jsonl_file = Path("enrichments.jsonl")

legal_milvus_uri = "file:/grag-milvus.db"

default_neo4j_uri = "bolt://localhost:7687"
neo4j_uri = os.environ.get("NEO4J_URI", default_neo4j_uri)
default_neo4j_username = "neo4j"
neo4j_username = os.environ.get("NEO4J_USERNAME", default_neo4j_username)
default_neo4j_password = "password"
neo4j_password = os.environ.get("NEO4J_PASSWORD", default_neo4j_password)


class Demo(Production):
    """
    A demonstration of Proscenium Scenes (with Characters and Props)
    interacting with an audience."""

    def __init__(self, admin_channel_id: str, console: Console) -> None:

        self.elementary_school_math_class = abacus.ElementarySchoolMathClass(
            admin_channel_id,
            console,
        )

        self.high_school_english_class = literature.HighSchoolEnglishClass(
            literature_milvus_uri,
            admin_channel_id,
            console=console,
        )

        self.law_library = legal.LawLibrary(
            default_docs_per_dataset,
            enrichment_jsonl_file,
            legal.doc_enrichments.default_delay,
            neo4j_uri,
            neo4j_username,
            neo4j_password,
            legal_milvus_uri,
            admin_channel_id,
            console=console,
        )

    def scenes(self) -> list[Scene]:

        return [
            self.elementary_school_math_class,
            self.high_school_english_class,
            self.law_library,
        ]

    def places(
        self,
        channel_name_to_id: dict,
    ) -> dict[str, Character]:

        channel_id_to_handler = {}
        for scene in self.scenes():
            channel_id_to_handler.update(scene.places(channel_name_to_id))

        return channel_id_to_handler


def make_production(admin_channel_id: str, console: Console) -> Demo:

    return Demo(admin_channel_id, console)
