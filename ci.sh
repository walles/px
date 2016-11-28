#!/bin/bash

set -o pipefail
set -e
set -x

if [ $# != 1 ] ; then
  # Run this script with two different Python interpreters
  "$0" python3
  "$0" python2
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

# FIXME: We want to add to the coverage report, not overwrite it. How do we do
# that?
PYTEST_ADDOPTS=--cov=px ./setup.py test

# Create px egg...
rm -rf dist
./setup.py bdist_egg
# ... and package everything in px.pex
pip install pex==1.1.15
rm -f px.pex
pex -r requirements.txt ./dist/px-*.egg -m px.px:main -o px.pex

pip install flake8==3.2.0
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
