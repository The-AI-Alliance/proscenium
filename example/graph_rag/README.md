# GraphRAG

Includes output as configured on March 11, 2025.

## Configuration

[example/graph_rag/config.py](./config.py)

## CLI

The demos are available via the CLI [commands](./typer_app.py)

```bash
python -m example.cli graph-rag --help
```

## Entity Extraction

`python -m example.cli graph-rag extract` [stdout](./output/extract_entities.out)

[entities.csv](./output/entities.csv) is an older copy that is upstream of the calls here

[entities-new.csv](./output/entities.csv) is a new version run with the config on 3/11/25

## Load Graph

`python -m example.cli graph-rag load-graph` [stdout](./output/load_entity_graph.out)

## Show Graph

`python -m example.cli graph-rag show-graph` [stdout](./output/show-graph.out)

## Load Resolver

`python -m example.cli graph-rag load-resolver` [stdout](./output/load_entity_resolver.out)

## Answer Question

`python -m example.cli graph-rag ask` [stdout](./output/answer_question.out)

## History

Taken from python notebook on a [branch](https://github.com/ibm-granite-community/granite-legal-cookbook/blob/158-legal-graph-rag/recipes/Graph/Entity_Extraction_from_NH_Caselaw.ipynb)
