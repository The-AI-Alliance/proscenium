from rich import print
from proscenium import header


def test_header():
    print(header())
    assert True, "Printed header"
