#!/bin/bash

set -o pipefail
set -e
set -x

# Make a virtualenv
ENVDIR="$(mktemp -d)"
function cleanup {
  rm -rf "${ENVDIR}"
}
trap cleanup EXIT

virtualenv "${ENVDIR}"
. "${ENVDIR}"/bin/activate

./setup.py test

./setup.py bdist_egg
pex -r <(pip freeze | grep -v '^px=') ./dist/px-*.egg -m px.px:main -o px.pex

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
