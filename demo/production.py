import logging
from pathlib import Path
import os

from rich.console import Console

from proscenium.core import Production
from proscenium.core import Character
from proscenium.core import Scene

from demo.settings import abacus, literature, legal

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
            legal.default_docs_per_dataset,
            enrichment_jsonl_file,
            legal.default_delay,
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
        channels_by_id: dict,
    ) -> dict[str, Character]:

        channel_name_to_id = {
            channel["name"]: channel["id"]
            for channel in channels_by_id.values()
            if channel.get("name")
        }

        channel_id_to_handler = {
            channel_name_to_id["abacus"]: self.elementary_school_math_class.abacus,
            channel_name_to_id[
                "literature"
            ]: self.high_school_english_class.literature_expert,
            channel_name_to_id["legal"]: self.law_library.law_librarian,
        }

        return channel_id_to_handler


production = Demo()
