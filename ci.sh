#!/bin/bash

set -o pipefail
set -e
set -x

# FIXME: Run code formatting checks

# FIXME: Run flake8

# Run all Python tests
./pants list | \
  xargs ./pants filter --filter-type=python_tests | \
  xargs ./pants test

echo
./pants run px
