---  
layout: default  
title: Proscenium
---  

## Proscenium

![logo](./assets/images/logo.png)

Proscenium is a small, experimental library of composable glue that allows for
succinct construction of enterprise AI applications.  It is in early development.

It is also set of simple demonstration applications that elucidate aspects of application and library design.

See the [repository](https://github.com/The-AI-Alliance/proscenium) on GitHub.

Currently, proscenium development prioritizes support for domains where
the creation and use of structured data is critical.

## Quickstart

There are two ways to get started quickly:

- [Command Line Interface](https://github.com/The-AI-Alliance/proscenium/blob/main/CLI.md) to demos, ither from a local repo clone or in a [new GitHub Codespace](https://github.com/codespaces/new/The-AI-Alliance/proscenium)

- [Notebooks](https://github.com/The-AI-Alliance/proscenium/tree/main/notebooks)

## Resources

For more background and future plans, see the [wiki](https://github.com/The-AI-Alliance/proscenium/wiki)

To find the Proscenium community, see the [discussions](https://github.com/The-AI-Alliance/proscenium/discussions)

## Goals

Proscenium is a library and a set of demonstration applications.
The applications illustrate a full picture of the AI application development and optimization process,
including:

- Data discovery, enrichment, and indexing
- Run-time inference patterns, including tool use
- Application characteristics that support auditability and accountability
- Decision support for product and data science teams
- Integration patterns for collaborative enterprise workflows including chat systems and document editors
- Production deployments

Proscenium does not provide any sample web applications, opting instead to demonstrate simple console applications.
Integrating with existing webapps and desktop software (eg chat clients) are a priority over implementating bespoke demo GUIs.

Proscenium is built on large mountains of other libraries.  The library itself is intended to be minimal.  We will happily delete large parts if they are redundant with clear de facto standards.  Further technical objectives include:

- Identify areas where innovation is still redefining interfaces
- Highlight designs that can limit the "blast radius" of those changes
- For users of frameworks, identify risk of lock-in
- Enumerate "glue code", libraries, or protocols that are missing from the ecosystem

Proscenium was started in February 2025 and is still in very early development.
