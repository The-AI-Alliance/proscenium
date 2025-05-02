import logging

log = logging.getLogger(__name__)


def format_chat_history(chat_history) -> str:
    delimiter = "-" * 80 + "\n"
    return delimiter.join(
        [
            f"{msg['sender']} to {msg['receiver']}:\n\n{msg['content']}\n\n"
            for msg in chat_history
        ]
    )
