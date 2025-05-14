from typing import Callable, Optional

import logging
import importlib
import yaml
from pathlib import Path
from rich.console import Console
from proscenium.core import Production

logging.getLogger(__name__).addHandler(logging.NullHandler())


def load_config(config_file_name: Path) -> dict:

    if not config_file_name.exists():
        raise FileNotFoundError(
            f"Configuration file {config_file_name} not found. "
            "Please provide a valid configuration file."
        )

    with open(config_file_name, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        return config


def production_from_config(
    config_file_name: Path,
    get_secret: Callable[[str, str], str],
    sub_console: Optional[Console] = None,
) -> tuple[Production, dict]:

    config = load_config(config_file_name)

    production_config = config.get("production", {})

    production_module_name = production_config.get("module", None)

    production_module = importlib.import_module(production_module_name, package=None)

    production = production_module.make_production(config, get_secret, sub_console)

    return production, config
