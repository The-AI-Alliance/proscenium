#!/usr/bin/env bash

pip install lapidarist --upgrade

echo "Literature Integration Test"

python -m demo.cli literature prepare --verbose

echo "" | python -m demo.cli literature ask --verbose

rm -f four_plays_of_aeschylus.txt walden.txt

rm -f milvus.db
