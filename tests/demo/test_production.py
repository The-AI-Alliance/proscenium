from typing import Callable
from typing import List
from typing import Optional
from typing import Generator
import logging

from rich.console import Console

from proscenium.core import Production
from proscenium.core import Character
from proscenium.core import Scene
from proscenium.core import Prop

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


class EchoCharacter(Character):

    def __init__(
        self,
        admin_channel_id: str,
    ):
        super().__init__(admin_channel_id=admin_channel_id)

    def wants_to_handle(self, channel_id: str, speaker_id: str, utterance: str) -> bool:

        log.info("handle? channel_id = %s, speaker_id = %s", channel_id, speaker_id)

        return True

    def handle(
        self, channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, utterance


class EchoScene(Scene):

    def __init__(
        self,
        channel_id: str,
        admin_channel_id: str,
        console: Optional[Console] = None,
    ):
        super().__init__()

        self.channel_id = channel_id
        self.console = console

        self.echo_character = EchoCharacter(
            admin_channel_id,
        )

    def props(self) -> List[Prop]:

        return []

    def characters(self) -> List[Character]:

        return [self.echo_character]

    def places(
        self,
        channel_name_to_id: dict,
    ) -> dict[str, Character]:

        return {channel_name_to_id[self.channel_id]: self.echo_character}


class Tests(Production):

    __test__ = False

    def __init__(
        self,
        admin_channel_id: str,
        echo_scene_channel: str,
        generator_model: str,
        control_flow_model: str,
        console: Console,
    ) -> None:

        self.echo_scene = EchoScene(
            echo_scene_channel,
            admin_channel_id,
            console,
        )

    def scenes(self) -> list[Scene]:

        return [self.echo_scene]

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
) -> tuple[Tests, dict]:

    production_config = config.get("production", {})
    scenes_config = production_config.get("scenes", {})
    echo_scene = scenes_config.get("echo_scene", {})

    inference_config = config.get("inference", {})
    slack_config = config.get("slack", {})

    return Tests(
        slack_config.get("admin_channel", get_secret("SLACK_ADMIN_CHANNEL")),
        echo_scene["channel"],
        inference_config["generator_model"],
        inference_config["control_flow_model"],
        console,
    )
