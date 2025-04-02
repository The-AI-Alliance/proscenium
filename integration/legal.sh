#!/usr/bin/env bash

echo "Legal Integration Test"

JSONL_FILE=test-enrichments.jsonl

echo "Enriching documents"

python -m demo.cli legal enrich \
  --docs-per-dataset=2 \
  --output=$JSONL_FILE

echo "Loading documents into Knowledge Graph"

python -m demo.cli legal load-graph \
  --input=$JSONL_FILE

echo "Displaying Knowledge Graph"

python -m demo.cli legal show-graph

echo "Loading fields into Milvus"

python -m demo.cli legal load-resolver

echo "Answer default legal question"

echo "" | python -m demo.cli legal ask

rm -f $JSONL_FILE

rm -f grag-milvus.db
