#!/usr/bin/env bash

PYTHONPATH=..

# pip install jupyter

for NOTEBOOK in $(find . -name "*.ipynb"); do
    echo "Running $NOTEBOOK"
    PYTHONPATH=$PYTHONPATH jupyter nbconvert --to markdown --execute --stdout "$NOTEBOOK" > "${NOTEBOOK%.ipynb}.md"
done
