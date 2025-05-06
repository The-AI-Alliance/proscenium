from typing import Generator
from typing import List
from typing import Optional

import logging

from rich.console import Console

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.core import Character
from proscenium.core import Prop
from proscenium.verbs.invoke import process_tools
from proscenium.scripts.tools import apply_tools

import demo.domains.abacus as domain
from demo.config import default_model_id

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)

tools = [Addition, Subtraction, Multiplication, Division]

tool_map, tool_desc_list = process_tools(tools)

system_message = """
Use the tools specified in this request to perform the arithmetic in the user's question.
Do not use any other tools.
"""


def props(console: Optional[Console]) -> List[Prop]:

    return []


class Abacus(Character):

    def __init__(self, admin_channel_id: str):
        super().__init__(admin_channel_id=admin_channel_id)

    def handle(
        self, channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, apply_tools(
            model_id=default_model_id,
            system_message=domain.system_message,
            message=utterance,
            tool_desc_list=domain.tool_desc_list,
            tool_map=domain.tool_map,
        )
