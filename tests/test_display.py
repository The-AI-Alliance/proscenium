from rich import print
from proscenium.verbs.display import header


def test_header():
    print(header())
    assert True, "Printed header"
