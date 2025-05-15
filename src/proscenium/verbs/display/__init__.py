from rich.text import Text


def header() -> Text:
    text = Text()
    text.append("Proscenium 🎭\n", style="bold")
    text.append("https://the-ai-alliance.github.io/proscenium/\n")
    # TODO version, timestamp, ...
    return text
