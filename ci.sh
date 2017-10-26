#!/bin/bash

set -o pipefail
set -e
set -x

if [ "$VIRTUAL_ENV" ] ; then
  echo 'ERROR: Already in a virtualenv, do "deactivate" first and try again'
  exit 1
fi

# Don't produce a binary if something goes wrong
trap "rm -f px.pex" ERR

if [ $# != 1 ] ; then
  if which shellcheck &> /dev/null ; then
    shellcheck ./*.sh ./*/*.sh
  fi

  source ./tests/installtest.sh

  # Run this script with two different Python interpreters
  . ./scripts/set-other-python.sh
  "$0" "$OTHER_PYTHON"
  "$0" "python"

  if ! head -n1 px.pex | grep -w python ; then
    echo
    echo "ERROR: px.pex should use \"python\" as its interpreter:"
    file px.pex
    false
    exit 1
  fi

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
virtualenv --python="$1" "${ENVDIR}"
# shellcheck source=/dev/null
. "${ENVDIR}"/bin/activate

# Fix tools versions
pip install -r requirements-dev.txt

if python --version 2>&1 | grep " 3" ; then
  # Verson of "python" binary is 3, do static type analysis. Mypy requires
  # Python 3, that's why we do this only on Python 3.
  pip install -r requirements-dev-py3.txt
  mypy ./*.py ./*/*.py
fi

# FIXME: We want to add to the coverage report, not overwrite it. How do we do
# that?
PYTEST_ADDOPTS="--cov=px -v" ./setup.py test

# Create px wheel...
rm -rf dist .deps/px-*.egg .deps/px-*.whl build/lib/px
./setup.py bdist_wheel --universal

# ... and package everything in px.pex
#
# Note that we have to --disable-cache here since otherwise changing the code
# without changing the "git describe" output won't change the resulting binary.
# And since that happens all the time during development we can't have that.
#
# Also note that we need to specify the --python-shebang to get "python" as an
# interpreter. Just passing --python (or nothing) defaults to following the
# "python" symlink and putting "2.7" here.
rm -f px.pex
pex --python-shebang="#!/usr/bin/env $1" --disable-cache -r requirements.txt ./dist/pxpx-*.whl -m px.px -o px.pex

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

./setup.py install
px bash
px --version
