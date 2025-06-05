---
layout: default  
title: Proscenium
---

## Proscenium

<img src="./assets/images/logo.png" align="left" width="180px" alt="proscenium logo"/>

Proscenium is an emerging library for building collaborative enterprise AI applications.

Sticking with the implied theater analogy,
the highest-level building block is a Production, which are composed of Scenes.
Scenes are composed of Characters and Props.

<img src="./assets/images/prometheus_slack.png" width="448px" alt="Prometheus question on Slack">

<br clear="left"/>

## Repository

See the [repository](https://github.com/The-AI-Alliance/proscenium) on GitHub.
Clone locally or start a [new GitHub Codespace](https://github.com/codespaces/new/The-AI-Alliance/proscenium)

[![PyPI version](https://img.shields.io/pypi/v/proscenium.svg)](https://pypi.org/project/proscenium/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/proscenium)](https://pypi.org/project/proscenium/)
[![CI](https://github.com/The-AI-Alliance/proscenium/actions/workflows/pytest.yml/badge.svg)](https://github.com/The-AI-Alliance/proscenium/actions/workflows/pytest.yml)
[![PyPI](https://img.shields.io/pypi/v/proscenium)](https://pypi.org/project/proscenium/)
[![License](https://img.shields.io/github/license/The-AI-Alliance/proscenium)](https://github.com/The-AI-Alliance/proscenium/tree/main?tab=Apache-2.0-1-ov-file#readme)
[![Issues](https://img.shields.io/github/issues/The-AI-Alliance/proscenium)](https://github.com/The-AI-Alliance/proscenium/issues)
[![GitHub stars](https://img.shields.io/github/stars/The-AI-Alliance/proscenium?style=social)](https://github.com/The-AI-Alliance/proscenium/stargazers)

## Colab Demos

- "Abacus" to use simple tools to respond to user questions. <a target="_blank" href="https://colab.research.google.com/github/The-AI-Alliance/proscenium/blob/main/notebooks/Abacus.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>
- "Literature" to use a vector database to store chunks of two books, and using those chunks to form a context for LLM inference based on a user question <a target="_blank" href="https://colab.research.google.com/github/The-AI-Alliance/proscenium/blob/main/notebooks/Literature.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/>
</a>
- "Slack" to attach Proscenium Productions (Scenes of Characters and Props) to Slack channels using a custom app. <a target="_blank" href="https://colab.research.google.com/github/The-AI-Alliance/proscenium/blob/main/notebooks/Slack.ipynb">
<img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

## Resources

For more background and future plans, see the [wiki](https://github.com/The-AI-Alliance/proscenium/wiki)

To find the Proscenium community, see the [discussions](https://github.com/The-AI-Alliance/proscenium/discussions)

## Use Cases

### Bartlebot

For federal case law research.  See the [website](https://the-ai-alliance.github.io/bartlebot/) and [repo](https://github.com/The-AI-Alliance/bartlebot)

## Library Design

Proscenium is being developed with an understanding that
details from specific enterprise application domains should be
prioritized in the early phases of its design.

The AI model, software, hardware, and cloud ecosystem is evolving rapidly.
Proscenium is designed to co-evolve with the ecosystem by keeping interfaces
simple and loosely-coupled.

The highest, app-level concepts are the theater-inspired classes.
Productions are composed of Scenes.
Scenes are composed of Characters and Props.

Under those higher-level classes are "patterns" for systems including:

- Document Enrichment
- Knowledge Graph Construction
- Entity Resolution
- RAG
- Graph RAG
- Tool Use

<img src="./assets/images/kg_diagram.png" width="600px" alt="kg diagram"/>

At the lowest level are "verbs" such as:
chunk, complete (inference), extract, and invoke (tools).
In many cases these are thin wrappers around well-known libraries.
