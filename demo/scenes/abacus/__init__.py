from typing import Generator
from typing import Optional

import logging
import json

from rich.console import Console

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.core import Character
from proscenium.core import Scene
from proscenium.core import control_flow_system_prompt
from proscenium.core import WantsToHandleResponse
from proscenium.verbs.complete import complete_simple
from proscenium.verbs.invoke import process_tools
from proscenium.patterns.tools import apply_tools

logging.getLogger(__name__).addHandler(logging.NullHandler())

log = logging.getLogger(__name__)

tools = [Addition, Subtraction, Multiplication, Division]

tool_map, tool_desc_list = process_tools(tools)

abacus_system_message = """
Use the tools specified in this request to perform the arithmetic in the user's question.
Do not use any other tools.
"""

wants_to_handle_template = """\
The text below is a user-posted message to a chat channel.
Determine if you, the AI assistant equipped with tools for arithmetic,
can find an arithmetic expression that you would be able to evaluate.
State a boolean value for whether you want to handle the message,
expressed in the specified JSON response format.
Only answer in JSON.

The user-posted message is:

{text}
"""


class Abacus(Character):
    """
    A character that can perform basic arithmetic operations.
    """

    def __init__(
        self, admin_channel_id: str, generator_model: str, control_flow_model: str
    ):
        super().__init__(admin_channel_id=admin_channel_id)
        self.generator_model = generator_model
        self.control_flow_model = control_flow_model

    def wants_to_handle(self, channel_id: str, speaker_id: str, utterance: str) -> bool:

        log.info("handle? channel_id = %s, speaker_id = %s", channel_id, speaker_id)

        response = complete_simple(
            model_id=self.control_flow_model,
            system_prompt=control_flow_system_prompt,
            user_prompt=wants_to_handle_template.format(text=utterance),
            response_format={
                "type": "json_object",
                "schema": WantsToHandleResponse.model_json_schema(),
            },
        )

        try:
            response_json = json.loads(response)
            result_message = WantsToHandleResponse(**response_json)
            log.info("wants_to_handle: result = %s", result_message.wants_to_handle)
            return result_message.wants_to_handle

        except Exception as e:

            log.error("Exception: %s", e)

    def handle(
        self, channel_id: str, speaker_id: str, utterance: str
    ) -> Generator[tuple[str, str], None, None]:

        yield channel_id, apply_tools(
            model_id=self.generator_model,
            system_message=abacus_system_message,
            message=utterance,
            tool_desc_list=tool_desc_list,
            tool_map=tool_map,
        )


class ElementarySchoolMathClass(Scene):
    """
    An elementary school math class where students can ask questions about arithmetic.
    """

    def __init__(
        self,
        channel_abacus: str,
        admin_channel_id: str,
        generator_model: str,
        control_flow_model: str,
        console: Optional[Console] = None,
    ):
        super().__init__()
        self.channel_abacus = channel_abacus
        self.admin_channel_id = admin_channel_id
        self.console = console
        self.abacus = Abacus(admin_channel_id, generator_model, control_flow_model)

    def characters(self) -> list[Character]:
        return [
            self.abacus,
        ]

    def places(
        self,
        channel_name_to_id: dict,
    ) -> dict[str, Character]:

        return {channel_name_to_id[self.channel_abacus]: self.abacus}
