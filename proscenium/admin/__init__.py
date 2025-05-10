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

    def __init__(self, admin_channel_id: str):
        super().__init__(admin_channel_id)
        self.admin_channel_id = admin_channel_id

    def wants_to_handle(self, channel_id: str, speaker_id: str, utterance: str) -> bool:
        return False

    def handle(
        channel_id: str,
        speaker_id: str,
        question: str,
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, "I am the administrator of this chat system."
