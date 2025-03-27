import pytest

from click import Command
from typer.main import get_command

from demo.cli import app


def _check_help_on_command(command: Command):
    """
    Check that this command (and any subcommands) has a non-empty help string.
    """

    assert (
        command.help is not None and command.help.strip() != ""
    ), f"Command '{command.name}' is missing a help string"

    # recurse into subcommands
    if hasattr(command, "commands"):
        for subcommand_name, subcommand in command.commands.items():
            _check_help_on_command(subcommand)


@pytest.mark.parametrize("command_name", list(get_command(app).commands.keys()))
def test_command_has_help(command_name: str):
    """
    Test each top-level command in the demo typer app to ensure
    it (and any subcommands) have help strings.
    """
    root_command: Command = get_command(app)
    command = root_command.commands[command_name]
    _check_help_on_command(command)
