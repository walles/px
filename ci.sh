#!/bin/bash

set -o pipefail
set -e
set -x

# Run all Python tests
./pants list | \
  xargs ./pants filter --filter-type=python_tests | \
  xargs ./pants test.pytest --coverage=modules:px --options=--durations=5

./pants binary px

echo
if unzip -qq -l dist/px.pex '*.so' ; then
  cat << EOF
  ERROR: There are natively compiled dependencies in the .pex, this makes
         distribution a lot harder. Please fix your dependencies.
EOF
  exit 1
fi

echo
./dist/px.pex

echo
./dist/px.pex $$

echo
./dist/px.pex --version
