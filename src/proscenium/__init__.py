import logging

from rich.text import Text

logging.getLogger(__name__).addHandler(logging.NullHandler())


def header() -> Text:
    text = Text()
    text.append("Proscenium 🎭\n", style="bold")
    text.append("https://the-ai-alliance.github.io/proscenium/\n")
    # TODO version, timestamp, ...
    return text
