from rich.text import Text


def header() -> Text:
    text = Text(
        """[bold]Proscenium[/bold] :performing_arts:
[bold]The AI Alliance[/bold]"""
    )
    # TODO version, timestamp, ...
    return text
