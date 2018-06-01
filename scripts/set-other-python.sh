# shellcheck shell=bash

if python --version 2>&1 | grep " 3" ; then
  # Verson of "python" binary is 3, just use "python2" as the other one
  OTHER_PYTHON="python2"
elif command -v python3.5 ; then
  # On Travis / Linux just "python3" gives us Python 3.2, which is too old
  OTHER_PYTHON="python3.5"
else
  # On OSX we get a recent Python3 from Homebrew, just go with the latest one
  OTHER_PYTHON="python3"
fi

if ! python --version &>/dev/null ; then
  echo 'ERROR: No "python" binary found'
  exit 1
fi

if ! "$OTHER_PYTHON" --version &>/dev/null ; then
  echo "ERROR: No \"$OTHER_PYTHON\" binary found"
  exit 1
fi

ONE_VERSION=$(python --version)
OTHER_VERSION=$($OTHER_PYTHON --version)
if [ "$ONE_VERSION" = "$OTHER_VERSION" ] ; then
  echo "ERROR: Both python and $OTHER_PYTHON are version $OTHER_VERSION"
  exit 1
fi
