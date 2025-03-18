# Proscenium: Framing Agents

Proscenium establishes a modular analysis of AI "Agents".
It is composed of several well-defined subsystems.

A few of the initial goals of this project include:

- Clarify how the components interact
- Identify areas where innovation is still redefining interfaces
- Highlight designs that can limit the "blast radius" of changes
- For users of frameworks, identify risk of lock-in
- Enumerate "glue code", libraries, or protocols that are missing from the ecosystem

## Subsystems

```text
      +------------------------------------------------------------------------------+
      |                                    Scripts                                   |
      +------------------------------------------------------------------------------+
      |                              Async IO & Actors (Aspirationally)              |
      +------------+--+------------+--+--------------+--+-------+--+-------+--+------+
VERBS |   Invoke   |  |  Complete  |  |   Remember   |  | Chunk |  | Parse |  | Load |
      +------------+  +------------+  +--------------+  +-------+  +-------+  +------+
      | APIs,      |  |  Inference |  | DB, RAM, ... |  | ...   |  | ...   |  | ...  |
      | Libraries, |  |  Providers |  +--------------+  +-------+  +-------+  +------+
      | ...        |  +------------+
      +------------+  |    LLMs    |
                      +------------+
```

## Methodology

These subsystems of Prosenium can be composed to mimic
patterns highlighted in modern agentic frameworks.

The include

- [Tool use](./proscenium/scripts/tools/)
- [RAG](./proscenium/scripts/rag/)
- [GraphRAG](./proscenium/scripts/graph_rag/)
- Reflection (coming soon)

Subsystem implementations used in these demos:

- Complete (Inference)
  - [AI Suite](https://github.com/andrewyng/aisuite)
- Invoke (Functions)
  - [Gofannon](https://github.com/The-AI-Alliance/gofannon)
- Remember
  - RAM: local module [`proscenium.remember`](./proscenium/remember.py)

- Actors
  - [Thespian](https://thespianpy.com/)

## Setup

```bash
git clone git@github.com:The-AI-Alliance/proscenium.git

cd proscenium

python -m venv venv

. venv/bin/activate

python -m pip install .

python -m proscenium.cli --help
```

or

```bash
git clone git@github.com:The-AI-Alliance/proscenium.git

cd proscenium

docker compose -f .devcontainer/docker-compose.yml up

docker exec -it devcontainer-devcontainer-1 sh -c "cd workspaces/proscenium && python -m proscenium.cli --help"
```

or

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new/The-AI-Alliance/proscenium)

## Command Line Interface

Proscenium uses [Typer](https://github.com/fastapi/typer) to provide
a command-line interface to some example applications built with
Proscenium scripts and sub-systems.

See the [CLI](./CLI.md) documentation.
