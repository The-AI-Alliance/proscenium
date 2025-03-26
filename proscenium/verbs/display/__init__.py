from rich.text import Text


def header() -> Text:
    text = Text()
    text.append("Proscenium 🎭\n", style="bold")
    text.append("The AI Alliance\n", style="bold")
    # TODO version, timestamp, ...
    return text
