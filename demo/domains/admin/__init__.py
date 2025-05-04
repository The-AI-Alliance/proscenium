from typing import Generator
from typing import Callable
from typing import List
from typing import Optional

import logging

from rich.console import Console

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)

system_message = """
You are an administrator of a chatbot.
"""


def prerequisites(console: Optional[Console]) -> List[Callable[[bool], None]]:

    return []


def make_handler(
    admin_channel_id: str,
) -> Callable[[tuple[str, str]], Generator[str, None, None]]:

    def handle(
        channel_id: str,
        speaker_id: str,  # pylint: disable=unused-argument
        question: str,
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, "I am the administrator of this chat system."

    return handle
