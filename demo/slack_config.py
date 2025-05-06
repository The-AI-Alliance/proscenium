from typing import List, Any

import logging
from pathlib import Path
import os

from rich.console import Console

from neo4j import GraphDatabase
from neo4j import Driver

from proscenium.core import Production
from proscenium.core import Prop
from proscenium.core import Character

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

    def __init__(self) -> None:
        pass

    def props(self, console: Console) -> List[Prop]:

        abacus_pres = abacus.props(console)

        literature_pres = literature.props(
            literature_milvus_uri,
            literature.default_collection_name,
            legal.default_embedding_model_id,
            console,
        )

        legal_pres = legal.props(
            legal.default_docs_per_dataset,
            enrichment_jsonl_file,
            legal.default_delay,
            neo4j_uri,
            neo4j_username,
            neo4j_password,
            legal_milvus_uri,
            legal.default_embedding_model_id,
            console,
        )

        return abacus_pres + literature_pres + legal_pres

    def places(
        self,
        channels_by_id: dict,
        admin_channel_id: str,
    ) -> tuple[dict[str, Character], Any]:

        log.info("Demo characters take places")

        channel_name_to_id = {
            channel["name"]: channel["id"]
            for channel in channels_by_id.values()
            if channel.get("name")
        }

        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_username, neo4j_password))

        channel_id_to_handler = {
            channel_name_to_id["abacus"]: abacus.Abacus(admin_channel_id),
            channel_name_to_id["literature"]: literature.LiteratureExpert(
                literature.default_generator_model_id,
                literature_milvus_uri,
                literature.default_embedding_model_id,
                admin_channel_id,
            ),
            channel_name_to_id["legal"]: legal.CaseLawExpert(
                driver, legal_milvus_uri, admin_channel_id
            ),
        }

        log.info(
            "Characters in place in channels: %s",
            ", ".join(list(channel_id_to_handler.keys())),
        )

        resources = driver

        return channel_id_to_handler, resources

    def exit(self, resources: Any) -> None:

        driver: Driver = resources

        driver.close()


production = Demo()
