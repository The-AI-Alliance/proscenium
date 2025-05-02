import logging
from gofannon.base import BaseTool

log = logging.getLogger(__name__)


def process_tools(tools: list[BaseTool]) -> tuple[dict, list]:
    applied_tools = [F() for F in tools]
    tool_map = {f.name: f.fn for f in applied_tools}
    tool_desc_list = [f.definition for f in applied_tools]
    return tool_map, tool_desc_list
