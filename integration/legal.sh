#!/usr/bin/env bash

echo "Legal Integration Test"

JSONL_FILE=test-enrichments.jsonl
MILVUS_URI=file://test-legal-milvus.db

echo "Enriching documents"

python -m demo.cli legal enrich --docs-per-dataset=2 --output=$JSONL_FILE --verbose

echo "Loading documents into Knowledge Graph"

python -m demo.cli legal load-graph --input=$JSONL_FILE --verbose

echo "Displaying Knowledge Graph"

python -m demo.cli legal display-graph --verbose

echo "Loading fields into Milvus"

python -m demo.cli legal load-resolver --verbose

echo "Answer default legal question"

echo "" | python -m demo.cli legal ask --verbose

rm -f $JSONL_FILE

rm -f test-legal-milvus.db
