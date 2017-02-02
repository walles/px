#!/bin/bash

set -o pipefail
set -e
set -x

# Don't produce a binary if something goes wrong
trap "rm -f px.pex" ERR

if [ $# != 1 ] ; then
  ./tests/installtest.sh

  # Run this script with two different Python interpreters
  if which python3.5 ; then
    # On Travis / Linux just "python3" gives us Python 3.2, which is too old
    PY3=python3.5
  else
    # On OSX we get a recent Python3 from Homebrew, just go with the latest one
    PY3=python3
  fi

  # Run tests on Python 3
  "$0" $PY3

  PY2=python
  # Verify that PY2 seems to be a Python 2 binary, will be caught by our ERR
  # trap if the grep fails
  $PY2 --version 2>&1 | grep " 2"

  # Run test on Python 2
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

./test.sh
