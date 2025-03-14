from rich import print
from thespian.actors import ActorSystem
from proscenium.display import print_header
import example.tools.config as config

print_header()

tool_applier = ActorSystem().createActor(config.ToolApplier)

answer = ActorSystem().ask(tool_applier, config.question, 1)

print(answer)
