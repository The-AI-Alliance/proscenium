# Proscenium Output

GraphRAG output for Proscenium as of March 11, 2025

[example.graph_rag.config.py](../example/graph_rag/config.py)

```bash
python -m example.graph_rag.extract_entities
```

[entities.csv](./entities.csv) is an older copy that is upstream of the calls here

[entities-new.csv](./entities.csv) is a new version run with the config on 3/11/25

[stdout](./extract_entities.out)

```bash
python -m example.graph_rag.load_entity_resolver
```

[stdout](./load_entity_resolver.out)

```bash
python -m example.graph_rag.load_entity_graph
```

[stdout](./load_entity_graph.out)

```bash
python -m example.graph_rag.answer_question
```

[stdout](./answer_question.out)
