from typing import Callable
import logging

from rich.console import Console

from proscenium import Production
from proscenium import Character
from proscenium import Scene

from demo.scenes import abacus, literature

log = logging.getLogger(__name__)


class Demo(Production):
    """
    A demonstration of Proscenium Scenes (with Characters and Props)
    interacting with an audience."""

    def __init__(
        self,
        admin_channel_id: str,
        elementary_school_math_class_channel: str,
        high_school_english_class_channel: str,
        literature_chunk_collection_name: str,
        milvus_uri: str,
        embedding_model: str,
        generator_model: str,
        control_flow_model: str,
        console: Console,
    ) -> None:

        self.elementary_school_math_class = abacus.ElementarySchoolMathClass(
            elementary_school_math_class_channel,
            admin_channel_id,
            generator_model,
            control_flow_model,
            console,
        )

        self.high_school_english_class = literature.HighSchoolEnglishClass(
            high_school_english_class_channel,
            milvus_uri,
            admin_channel_id,
            literature_chunk_collection_name,
            embedding_model,
            generator_model,
            control_flow_model,
            console=console,
        )

    def scenes(self) -> list[Scene]:

        return [
            self.elementary_school_math_class,
            self.high_school_english_class,
        ]

    def places(
        self,
        channel_name_to_id: dict,
    ) -> dict[str, Character]:

        channel_id_to_handler = {}
        for scene in self.scenes():
            channel_id_to_handler.update(scene.places(channel_name_to_id))

        return channel_id_to_handler


def make_production(
    config: dict, get_secret: Callable[[str, str], str], console: Console
) -> tuple[Demo, dict]:

    production_config = config.get("production", {})
    scenes_config = production_config.get("scenes", {})
    elementary_school_math_class = scenes_config.get("elementary_school_math_class", {})
    high_school_english_class = scenes_config.get("high_school_english_class", {})

    inference_config = config.get("inference", {})
    vectors_config = config.get("vectors", {})
    slack_config = config.get("slack", {})

    return Demo(
        slack_config.get("admin_channel", get_secret("SLACK_ADMIN_CHANNEL")),
        elementary_school_math_class["channel"],
        high_school_english_class["channel"],
        high_school_english_class["chunk_collection"],
        vectors_config["milvus_uri"],
        vectors_config["embedding_model"],
        inference_config["generator_model"],
        inference_config["control_flow_model"],
        console,
    )
