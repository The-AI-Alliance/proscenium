from typing import Generator
from typing import Optional
import logging
from rich.console import Console

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)


class Prop:
    """
    A `Prop` is a resource available to the `Character`s in a `Scene`.
    """

    def __init__(
        self,
        console: Optional[Console] = None,
    ):
        self.console = console

    def name(self) -> str:
        return self.__class__.__name__

    def description(self) -> str:
        return self.__doc__ or ""

    def already_built(self) -> bool:
        return False

    def build(self, force: bool = False) -> None:
        pass


class Character:
    """
    A `Character` is a participant in a `Scene` that `handle`s utterances from the
    scene by producing its own utterances."""

    def __init__(self, admin_channel_id: str):
        self.admin_channel_id = admin_channel_id

    def name(self) -> str:
        return self.__class__.__name__

    def description(self) -> str:
        return self.__doc__ or ""

    def handle(
        channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:
        pass


class Scene:
    """
    A `Scene` is a setting in which `Character`s interact with each other and
    with `Prop`s. It is a container for `Character`s and `Prop`s.
    """

    def __init__(self):
        pass

    def name(self) -> str:
        return self.__class__.__name__

    def description(self) -> str:
        return self.__doc__ or ""

    def props(self) -> list[Prop]:
        return []

    def characters(self) -> list[Character]:
        return []

    def places(self) -> dict[str, Character]:
        pass

    def curtain(self) -> None:
        pass


class Production:
    """
    A `Production` is a collection of `Scene`s."""

    def __init__(self):
        pass

    def name(self) -> str:
        return self.__class__.__name__

    def description(self) -> str:
        return self.__doc__ or ""

    def scenes(self) -> list[Scene]:
        return []

    def curtain(self) -> None:
        for scene in self.scenes():
            scene.curtain()
