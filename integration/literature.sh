#!/usr/bin/env bash

echo "Literature Integration Test"

python -m demo.cli literature prepare

echo "" | python -m demo.cli literature ask

rm -f four_plays_of_aeschylus.txt

rm -f milvus.db
