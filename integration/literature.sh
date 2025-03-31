#!/usr/bin/env bash

echo "Literature Integration Test"

python -m demo.cli literature prepare

echo "" | python -m demo.cli literature ask

rm -f four_plays_of_aeschylus.txt walden.txt

rm -f milvus.db
