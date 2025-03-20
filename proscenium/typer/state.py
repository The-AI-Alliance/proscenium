
from rich.console import Console

class AppState:

    def __init__(
        self,
        verbose: bool = False):

        self.console = Console()
        self.verbose = verbose

