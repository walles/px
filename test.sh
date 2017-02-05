#!/bin/bash

set -o pipefail
set -e
set -x

# Don't produce a binary if something goes wrong
trap "rm -f px.pex" ERR

function do-tests() {
  PYTHON=$1
  ENVDIR=".${PYTHON}-env"

  test -d "$ENVDIR" || virtualenv "$ENVDIR" --python=$PYTHON
  # shellcheck source=/dev/null
  . "$ENVDIR"/bin/activate

  # Fix tools versions
  pip install -r requirements-dev.txt

  # Run tests
  ./setup.py test

  deactivate
}

source ./scripts/set-py2-p3.sh
do-tests $PY3
do-tests $PY2

ENVDIR=".${PY2}-env"
# shellcheck source=/dev/null
. "$ENVDIR"/bin/activate

flake8 px tests setup.py

# Create px wheel...
./setup.py bdist_wheel --universal

# ... and package everything in px.pex
#
# Note that we have to --disable-cache here since otherwise changing the code
# without changing the "git describe" output won't change the resulting binary.
# And since that happens all the time during development we can't have that.
rm -f px.pex
pex --disable-cache -r requirements.txt ./dist/px-*.whl -m px.px:main -o px.pex

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
