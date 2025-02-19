# Proscenium: Framing Agents as Actors

Proscenium establishes a modular analysis of AI "Agents".
It is composed of several well-defined subsystems.

- Clarify how the components interact
- Identify areas where innovation is still redefining interfaces
- Highlight designs that can limit the "blast radius" of changes
- For users of frameworks, identify risk of lock-in

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

## Implementation

Examples and bindings for several real implementations of these
subsystem are provided in this repository.

- Actors
  - [Thespian](https://thespianpy.com/)
- Inference
  - [AI Suite](https://github.com/andrewyng/aisuite)
- Functions
  - [Gofannon](https://github.com/The-AI-Alliance/gofannon)
- Memory
  - RAM: local module [`proscenium.memory`](proscenium/memory.py)

## Examples

The purpose of this repository is to show several examples of these sub-systems
working together in a way that mimics patterns highlighted in modern agentic frameworks.

The will include

- Tool use
- Reflection
- RAG
- GraphRAG

## Talk

The [`walkthrough`](walkthrough/) directory contains scripts that demonstrate
the role that each plays by building a running example one layer at a time.

## Setup

```bash
python3.11 -m venv venv

. venv/bin/activate

pip install -r requirements.txt
pip install git+https://github.com/The-AI-Alliance/gofannon.git
```
