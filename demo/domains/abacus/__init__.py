from typing import Generator
from typing import Callable
from typing import List
from typing import Optional

import logging

from rich.console import Console

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

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


def prerequisites(console: Optional[Console]) -> List[Callable[[bool], None]]:

    return []


def make_handler() -> Callable[[str], Generator[str, None, None]]:

    def handle(question: str) -> Generator[str, None, None]:

        yield apply_tools(
            model_id=default_model_id,
            system_message=domain.system_message,
            message=question,
            tool_desc_list=domain.tool_desc_list,
            tool_map=domain.tool_map,
        )

    return handle
