# Proscenium: Framing Agents as Actors

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
+------------------------------------------------------------+
|                   Interaction Patterns                     |
+------------------------------------------------------------+
|                          Actors                            |
+--------------+---+----------------------+---+--------------+
|   Functions  |   |      Inference       |   |   Memory     |
+--------------+   +----------------------+   +--------------+
| APIs,        |   |  Inference Providers |   | DB, RAM, ... |
| Libraries,   |   +----------------------+   +--------------+
| ...          |   |         LLMs         |
+--------------+   +----------------------+
```

## Methodology

The purpose of this repository is to show several examples of these sub-systems
working together in a way that mimics patterns highlighted in modern agentic frameworks.

The will include

- Tool use
- Reflection
- RAG
- GraphRAG
- ...

Subsystem implementations used in these demos:

- Actors
  - [Thespian](https://thespianpy.com/)
- Inference
  - [AI Suite](https://github.com/andrewyng/aisuite)
- Functions
  - [Gofannon](https://github.com/The-AI-Alliance/gofannon)
- Memory
  - RAM: local module [`proscenium.memory`](proscenium/memory.py)

## Setup

```bash
python3.11 -m venv venv

. venv/bin/activate

pip install git+https://github.com/The-AI-Alliance/proscenium.git
```

or

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new/The-AI-Alliance/proscenium)
