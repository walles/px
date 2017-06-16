# shellcheck shell=bash

if which python3.5 ; then
  # On Travis / Linux just "python3" gives us Python 3.2, which is too old
  PY3=python3.5
else
  # On OSX we get a recent Python3 from Homebrew, just go with the latest one
  PY3=python3
fi

PY2=python2
# Verify that PY2 seems to be a Python 2 binary, will be caught by our ERR
# trap if the grep fails
if ! $PY2 --version 2>&1 | grep " 2" ; then
  echo ERROR: No Python 2 interpreter found
  exit 1
fi
