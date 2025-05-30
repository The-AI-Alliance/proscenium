import os
import sys
import logging
import time
import pytest
from pathlib import Path
from rich.console import Console

from proscenium.bin import production_from_config
from proscenium.interfaces.slack import SlackProductionProcessor

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s  %(levelname)-8s %(name)s: %(message)s",
    level=logging.WARNING,
)

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
logging.getLogger("proscenium").setLevel(logging.INFO)
logging.getLogger("demo").setLevel(logging.INFO)

console = Console()

config_file = Path("tests/demo/tests.yml")


@pytest.fixture
def setup_slack():

    print("\nSetting up Slack Processor...")

    production, config = production_from_config(config_file, os.environ.get, console)

    console.print("Preparing props...")
    production.prepare_props()
    console.print("Props are up-to-date.")

    slack_admin_channel = config.get("slack", {}).get("admin_channel", None)
    slack_production_processor = SlackProductionProcessor(
        production,
        slack_admin_channel,
        console,
    )

    time.sleep(2)

    yield slack_production_processor

    print("\nTearing down resources...")
    slack_production_processor.shutdown()


# TODO check for startup messages


def test_admin(setup_slack):
    assert setup_slack.admin.channel == "deus-ex-machina", "Admin channel is set"


# TODO send message as another user and check that it is echoed back
