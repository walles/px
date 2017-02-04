#!/bin/bash

set -o pipefail
set -e
set -x

# Don't produce a binary if something goes wrong
trap "rm -f px.pex" ERR

if [ $# != 1 ] ; then
  source ./tests/installtest.sh

  # Run this script with two different Python interpreters
  . ./scripts/set-py2-p3.sh
  "$0" $PY3
  "$0" $PY2

  echo
  echo "All tests passed!"
  echo
  exit
fi

# Make a virtualenv
ENVDIR="$(mktemp -d)"
function cleanup {
  rm -rf "${ENVDIR}"
}
trap cleanup EXIT

# Expect the first argument to be a Python interpreter
virtualenv --python=$1 "${ENVDIR}"
# shellcheck source=/dev/null
. "${ENVDIR}"/bin/activate

# Fix tools versions
pip install -r requirements-dev.txt

# FIXME: We want to add to the coverage report, not overwrite it. How do we do
# that?
PYTEST_ADDOPTS=--cov=px ./setup.py test

# Create px wheel...
rm -rf dist .deps/px-*.egg .deps/px-*.whl build/lib/px
./setup.py bdist_wheel --universal
# ... and package everything in px.pex
rm -f px.pex
pex --disable-cache -r requirements.txt ./dist/px-*.whl -m px.px:main -o px.pex

flake8 px tests setup.py

echo
if unzip -qq -l px.pex '*.so' ; then
  cat << EOF
  ERROR: There are natively compiled dependencies in the .pex, this makes
         distribution a lot harder. Please fix your dependencies.
EOF
  exit 1
fi

echo
./px.pex

echo
./px.pex $$

echo
./px.pex --version
