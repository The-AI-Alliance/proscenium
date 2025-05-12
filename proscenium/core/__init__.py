from typing import Generator
from typing import Optional
import logging

from pydantic import BaseModel, Field
from rich.console import Console

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)

control_flow_system_prompt = """
You control the workflow of an AI assistant.  You evaluate user-posted messages and decide what the next step is.
"""


class WantsToHandleResponse(BaseModel):
    """
    The response to whether the Character wants to handle the provided utterance.
    """

    wants_to_handle: bool = Field(
        description="A boolean indicating whether the Character wants to handle the provided utterance.",
    )


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

    def curtain_up_message(self) -> str:
        return f"- {self.name()}, {self.description().strip()}"

    def already_built(self) -> bool:
        return False

    def build(self) -> None:
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

    def curtain_up_message(self) -> str:
        return f"- {self.name()}, {self.description().strip()}"

    def wants_to_handle(self, channel_id: str, speaker_id: str, utterance: str) -> bool:
        return False

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

    def curtain_up_message(self) -> str:

        characters_msg = "\n".join(
            [character.curtain_up_message() for character in self.characters()]
        )

        props_msg = "\n".join([prop.curtain_up_message() for prop in self.props()])

        return f"""
Scene: {self.name()}, {self.description().strip()}

Characters:
{characters_msg}

Props:
{props_msg}
"""

    def props(self) -> list[Prop]:
        return []

    def prepare_props(self, force_rebuild: bool = False) -> None:
        for prop in self.props():
            if force_rebuild:
                prop.build()
            elif not prop.already_built():
                log.info("Prop %s not built. Building it now.", prop.name())
                prop.build()

    def characters(self) -> list[Character]:
        return []

    def places(self) -> dict[str, Character]:
        pass

    def curtain(self) -> None:
        pass


class Production:
    """
    A `Production` is a collection of `Scene`s."""

    def __init__(self, admin_channel_id: str, console: Optional[Console] = None):
        self.admin_channel_id = admin_channel_id
        self.console = console

    def name(self) -> str:
        return self.__class__.__name__

    def description(self) -> str:
        return self.__doc__ or ""

    def prepare_props(self, force_rebuild: bool = False) -> None:
        if force_rebuild:
            log.info("Forcing rebuild of all props.")
        else:
            log.info("Building any missing props...")

        for scene in self.scenes():
            scene.prepare_props(force_rebuild=force_rebuild)

    def curtain_up_message(self) -> str:

        scenes_msg = "\n\n".join(
            [scene.curtain_up_message() for scene in self.scenes()]
        )

        return f"""Production: {self.name()}, {self.description().strip()}

{scenes_msg}"""

    def scenes(self) -> list[Scene]:
        return []

    def curtain(self) -> None:
        for scene in self.scenes():
            scene.curtain()
