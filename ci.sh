#!/bin/bash

set -o pipefail
set -e
set -x

# Run all Python tests
./pants list | \
  xargs ./pants filter --filter-type=python_tests | \
  xargs ./pants test

echo
./pants run px
