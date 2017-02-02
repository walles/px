#!/bin/bash

set -o pipefail
set -e
set -x

# Don't produce a binary if something goes wrong
trap "rm -f px.pex" ERR

if [ ! "$VIRTUAL_ENV" ] ; then
  # Not already in a Virtualenv...
  ENVDIR=env

  if [ ! -d "$ENVDIR" ] ; then
    # Virtualenv doesn't exist, create one
    virtualenv "$ENVDIR"
  fi

  # shellcheck source=/dev/null
  . "${ENVDIR}"/bin/activate
fi

# Fix tools versions
pip install pip==8.1.2 setuptools==29.0.1 wheel==0.24.0

# FIXME: We want to add to the coverage report, not overwrite it. How do we do
# that?
PYTEST_ADDOPTS=--cov=px ./setup.py test

# Create px wheel...
rm -rf dist .deps/px-*.egg .deps/px-*.whl build/lib/px
./setup.py bdist_wheel --universal
# ... and package everything in px.pex
pip install pex==1.2.1
rm -f px.pex
pex --disable-cache -r requirements.txt ./dist/px-*.whl -m px.px:main -o px.pex

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
