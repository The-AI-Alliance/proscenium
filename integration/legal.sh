#!/usr/bin/env bash

echo "Legal Integration Test"

set +x

JSONL_FILE=test-enrichments.jsonl

python -m demo.cli legal enrich \
  --docs-per-dataset=2 \
  --output=$JSONL_FILE

python -m demo.cli legal load-graph \
  --input=$JSONL_FILE

python -m demo.cli legal show-graph

python -m demo.cli legal load-resolver

echo "" | python -m demo.cli legal ask

rm -f $JSONL_FILE

rm -f grag-milvus.db
