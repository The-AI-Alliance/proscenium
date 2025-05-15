#!/usr/bin/env bash

# Lapidarist is not directly needed for this test, but it a dependency
# of the demo package.  A future refactoring will remove this dependency.
pip install lapidarist --upgrade

echo "Abacus Integration Test"

echo "What is 1 + 1?" | python -m demo.cli abacus ask --verbose
