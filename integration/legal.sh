#!/usr/bin/env bash

echo "Legal Integration Test"

python -m demo.cli legal enrich

python -m demo.cli legal load-graph

python -m demo.cli legal show-graph

python -m demo.cli legal load-resolver

echo "" | python -m demo.cli legal ask

rm -f enrichments.csv

rm -f grag-milvus.db
