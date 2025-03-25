# Proscenium Command Line Interface

## Help

```bash
python -m proscenium.cli --help
```

## Abacus (Tool Use)

The "Abacus" app example below uses arithmetic operators as provided by
[Gofannon](https://github.com/The-AI-Alliance/gofannon)

### Without Actors

`python -m proscenium.cli abacus ask` [stdout](./output/abacus/ask.out)

### With Actors

`python -m proscenium.cli abacus-actor ask` [stdout](./output/abacus/ask-actor.out)

## Literature (RAG)

```bash
python -m proscenium.cli literature --help
```

### Build vector database

`python -m proscenium.cli literature build-vector-db` [stdout](./output/literature/build-vector-db.out)

### Ask Question

`python -m proscenium.cli literature ask` [stdout](./output/literature/ask.out)

## Legal (GraphRAG)

```bash
python -m proscenium.cli legal --help
```

### Entity Extraction

`python -m proscenium.cli legal extract` [stdout](./output/legal/extract_entities.out)

[entities.csv](./output/legal/entities.csv) is an older copy that is upstream of the calls here

[entities-new.csv](./output/legal/entities.csv) is a new version run with the config on 3/11/25

### Load Graph

`python -m proscenium.cli legal load-graph` [stdout](./output/legal/load_entity_graph.out)

### Show Graph

`python -m proscenium.cli legal show-graph` [stdout](./output/legal/show-graph.out)

### Load Resolver

`python -m proscenium.cli legal load-resolver` [stdout](./output/legal/load_entity_resolver.out)

### Ask Question

`python -m proscenium.cli legal ask` [stdout](./output/legal/answer_question.out)

### History

Taken from python notebook on a [branch](https://github.com/ibm-granite-community/granite-legal-cookbook/blob/158-legal-graph-rag/recipes/Graph/Entity_Extraction_from_NH_Caselaw.ipynb)
