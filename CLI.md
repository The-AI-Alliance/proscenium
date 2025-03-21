# Proscenium Command Line Interface

## Help

```bash
python -m proscenium.cli --help
```

## Tool Use

The "abacus" app example below uses arithmetic operators as provided by
[Gofannon](https://github.com/The-AI-Alliance/gofannon)

### Without Actors

`python -m proscenium.cli abacus ask` [stdout](./output/abacus/ask.out)

### With Actors

`python -m proscenium.cli abacus-actor ask` [stdout](./output/abacus/ask-actor.out)

## RAG

```bash
python -m proscenium.cli rag --help
```

### Build vector database

`python -m proscenium.cli rag build-vector-db` [stdout](./output/rag/build-vector-db.out)

### Ask Question

`python -m proscenium.cli rag ask` [stdout](./output/rag/ask.out)

## GraphRAG

```bash
python -m proscenium.cli graph-rag --help
```

### Entity Extraction

`python -m proscenium.cli graph-rag extract` [stdout](./output/graph_rag/extract_entities.out)

[entities.csv](./output/graph_rag/entities.csv) is an older copy that is upstream of the calls here

[entities-new.csv](./output/graph_rag/entities.csv) is a new version run with the config on 3/11/25

### Load Graph

`python -m proscenium.cli graph-rag load-graph` [stdout](./output/graph_rag/load_entity_graph.out)

### Show Graph

`python -m proscenium.cli graph-rag show-graph` [stdout](./output/graph_rag/show-graph.out)

### Load Resolver

`python -m proscenium.cli graph-rag load-resolver` [stdout](./output/graph_rag/load_entity_resolver.out)

### Answer Question

`python -m proscenium.cli graph-rag ask` [stdout](./output/graph_rag/answer_question.out)

### History

Taken from python notebook on a [branch](https://github.com/ibm-granite-community/granite-legal-cookbook/blob/158-legal-graph-rag/recipes/Graph/Entity_Extraction_from_NH_Caselaw.ipynb)
