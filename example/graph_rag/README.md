# GraphRAG

Includes output as configured on March 11, 2025.

## Configuration

[example/graph_rag/config.py](./config.py)

## Entity Extraction

`python -m example.graph_rag.extract_entities` [stdout](./output/extract_entities.out)

[entities.csv](./output/entities.csv) is an older copy that is upstream of the calls here

[entities-new.csv](./output/entities.csv) is a new version run with the config on 3/11/25

## Load Resolver

`python -m example.graph_rag.load_entity_resolver` [stdout](./output/load_entity_resolver.out)

## Load Graph

`python -m example.graph_rag.load_entity_graph` [stdout](./output/load_entity_graph.out)

## Answer Question

`python -m example.graph_rag.answer_question` [stdout](./output/answer_question.out)

## History

Taken from python notebook on a [branch](https://github.com/ibm-granite-community/granite-legal-cookbook/blob/158-legal-graph-rag/recipes/Graph/Entity_Extraction_from_NH_Caselaw.ipynb)
