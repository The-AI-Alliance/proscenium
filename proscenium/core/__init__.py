from typing import Generator
from typing import Optional
import logging
from rich.console import Console

logging.getLogger(__name__).addHandler(logging.NullHandler())


class Prop:

    def __init__(
        self,
        console: Optional[Console] = None,
    ):
        self.console = console

    def build(self, force: bool = False) -> None:
        pass


class Character:

    def __init__(self, admin_channel_id: str):
        self.admin_channel_id = admin_channel_id

    def handle(
        channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:
        pass


class Scene:

    def __init__(self):
        pass


class Production:

    def __init__(self):
        pass

    def props(self) -> list[Prop]:
        return []

    def places(self) -> None:
        pass

    def exit(self) -> None:
        pass
