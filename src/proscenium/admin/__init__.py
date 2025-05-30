from typing import Generator
from typing import List
from typing import Optional

import logging

from proscenium.core import Prop
from proscenium.core import Character
from rich.console import Console

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)

system_message = """
You are an administrator of a chatbot.
"""


def props(console: Optional[Console]) -> List[Prop]:

    return []


class Admin(Character):

    def __init__(self, channel_id: str, channel: str):
        super().__init__(channel_id)
        self.channel_id = channel_id
        self.channel = channel

        log.info("Admin handler started %s %s.", self.channel, self.channel_id)

    def wants_to_handle(self, channel_id: str, speaker_id: str, utterance: str) -> bool:
        return False

    def handle(
        channel_id: str,
        speaker_id: str,
        question: str,
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, "I am the administrator of this chat system."
