from typing import Generator
from typing import Callable

from gofannon.basic_math.addition import Addition
from gofannon.basic_math.subtraction import Subtraction
from gofannon.basic_math.multiplication import Multiplication
from gofannon.basic_math.division import Division

from proscenium.verbs.invoke import process_tools
from proscenium.scripts.tools import apply_tools

import demo.domains.abacus as domain
from demo.config import default_model_id


tools = [Addition, Subtraction, Multiplication, Division]

tool_map, tool_desc_list = process_tools(tools)

system_message = """
Use the tools specified in this request to perform the arithmetic in the user's question.
Do not use any other tools.
"""


def make_handler(verbose: bool = False) -> Callable[[str], Generator[str, None, None]]:

    def handle(question: str) -> Generator[str, None, None]:

        yield apply_tools(
            model_id=default_model_id,
            system_message=domain.system_message,
            message=question,
            tool_desc_list=domain.tool_desc_list,
            tool_map=domain.tool_map,
            rich_output=verbose,
        )

    return handle
