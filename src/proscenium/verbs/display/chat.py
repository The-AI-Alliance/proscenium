from rich.table import Table


def messages_table(messages: list) -> Table:

    table = Table(title="Messages in Chat Context", show_lines=True)
    table.add_column("Role", justify="left")
    table.add_column("Content", justify="left")
    for message in messages:
        if type(message) is dict:
            role = message["role"]
            content = ""
            if role == "tool":
                content = f"""tool call id = {message['tool_call_id']}
fn name = {message['name']}
result = {message['content']}"""
            elif role == "assistant":
                content = f"""{str(message)}"""
            else:
                content = message["content"]
            table.add_row(role, content)
        else:
            role = message.role
            content = ""
            if role == "tool":
                content = f"""tool call id = {message.tool_call_id}
fn name = {message.name}
result = {message['content']}"""
            elif role == "assistant":
                content = f"""{str(message)}"""
            else:
                content = message.content
            table.add_row(role, content)

    return table
