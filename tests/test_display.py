from rich import print
from proscenium.display import print_header


def test_header():
    print_header()
    assert True, "Printed header"
