#!/bin/bash

set -o pipefail
set -e

if [ "$VIRTUAL_ENV" ] ; then
  echo 'ERROR: Already in a virtualenv, do "deactivate" first and try again'
  exit 1
fi

# Don't produce a binary if something goes wrong
trap "rm -f px.pex" ERR

function do-tests() {
  PYTHON=$1
  ENVDIR=".${PYTHON}-env"

  test -d "$ENVDIR" || virtualenv "$ENVDIR" --python="$PYTHON"
  # shellcheck source=/dev/null
  . "$ENVDIR"/bin/activate

  # Fix tools versions
  pip install -r requirements-dev.txt

  if python --version 2>&1 | grep " 3" ; then
    # Verson of "python" binary is 3, do static type analysis. Mypy requires
    # Python 3, that's why we do this only on Python 3.
    pip install -r requirements-dev-py3.txt
    mypy ./*.py ./*/*.py
  fi

  # Run tests
  ./setup.py test

  deactivate
}

if which shellcheck &> /dev/null ; then
  shellcheck ./*.sh ./*/*.sh
fi

source ./scripts/set-other-python.sh
do-tests "$OTHER_PYTHON"
do-tests "python"

ENVDIR=".python-env"
# shellcheck source=/dev/null
. "$ENVDIR"/bin/activate

flake8 px tests setup.py

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
pex --python-shebang="#!/usr/bin/env python" --disable-cache -r requirements.txt ./dist/pxpx-*.whl -m px.px -o px.pex

echo
if unzip -qq -l px.pex '*.so' ; then
  cat << EOF
  ERROR: There are natively compiled dependencies in the .pex, this makes
         distribution a lot harder. Please fix your dependencies.
EOF
  exit 1
fi

if ! head -n1 px.pex | grep -w python ; then
  echo
  echo "ERROR: px.pex should use \"python\" as its interpreter:"
  file px.pex
  false
  exit 1
fi

echo
./px.pex bash

# Validate what pip install will give us
./setup.py install
px $$
px --version
