#!/bin/bash

set -o pipefail
set -e
set -x

MYDIR=$(cd "$(dirname "$0")" ; pwd)

if [ "$VIRTUAL_ENV" ] ; then
  echo 'ERROR: Already in a virtualenv, do "deactivate" first and try again'
  exit 1
fi

# Don't produce a binary if something goes wrong
trap "rm -f px.pex" ERR

if [ $# != 1 ] ; then
  if command -v shellcheck &> /dev/null ; then
    shellcheck ./*.sh ./*/*.sh
  fi

  source ./tests/installtest.sh

  # Run this script with two different Python interpreters
  . ./scripts/set-other-python.sh
  "${MYDIR}/scripts/parallelize.py" "$0 $OTHER_PYTHON" "$0 python"
  cp .python-env/px.pex "${MYDIR}"

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

PYTHONBIN="$1"

# Prepare for making a virtualenv
ENVDIR="${MYDIR}/.${PYTHONBIN}-env"
for DEP in "$(command -v virtualenv)" "${PYTHON}" requirements*.txt ; do
  if [ "$DEP" -nt "${ENVDIR}" ] ; then
    # Drop our virtualenv, it's older than one of its dependencies
    rm -rf "$ENVDIR"
  fi
done

if [ ! -d "${ENVDIR}" ]; then
  # No virtualenv, set it up
  virtualenv --python="${PYTHONBIN}" "${ENVDIR}"
  # shellcheck source=/dev/null
  . "${ENVDIR}"/bin/activate

  pip install -r requirements.txt

  # Fix tools versions
  pip install -r requirements-dev.txt

  if python --version 2>&1 | grep " 3" ; then
    pip install -r requirements-dev-py3.txt
  fi
else
  # Just activate the existing virtualenv
  # shellcheck source=/dev/null
  . "${ENVDIR}"/bin/activate
fi

# Call setup.py here to ensure version.py has been generated before we do anything
# else.
./setup.py check

if python --version 2>&1 | grep " 3" ; then
  # Verson of "python" binary is 3, do static type analysis. Mypy requires
  # Python 3, that's why we do this only on Python 3.
  mypy ./*.py ./*/*.py
  mypy ./*.py ./*/*.py --python-version=2.7
fi

flake8 px tests scripts setup.py

# We're getting DeprecationWarnings from pytest 4.2.0, which is the latest
# version at the time of writing this comment.
# FIXME: Go for just -Werror as soon as possible
python -Werror -Wdefault::DeprecationWarning -Wdefault::PendingDeprecationWarning ./setup.py test

# Create px wheel...
rm -rf dist "${ENVDIR}"/pxpx-*.whl build/lib/px
./setup.py bdist_wheel --universal --dist-dir="${ENVDIR}"

# ... and package everything in px.pex
#
# Note that we have to --disable-cache here since otherwise changing the code
# without changing the "git describe" output won't change the resulting binary.
# And since that happens all the time during development we can't have that.
#
# Also note that we need to specify the --python-shebang to get "python" as an
# interpreter. Just passing --python (or nothing) defaults to following the
# "python" symlink and putting "2.7" here.
PX_PEX="${ENVDIR}/px.pex"
rm -f "${PX_PEX}"
pex --python-shebang="#!/usr/bin/env $1" --disable-cache -r requirements.txt "${ENVDIR}"/pxpx-*.whl -m px.px -o "${PX_PEX}"

echo
if unzip -qq -l "${PX_PEX}" '*.so' ; then
  cat << EOF
  ERROR: There are natively compiled dependencies in the .pex, this makes
         distribution a lot harder. Please fix your dependencies.
EOF
  exit 1
fi

echo
python -Werror -Wdefault:'the imp module' "${PX_PEX}"

echo
test "$("${PX_PEX}" --version)" = "$(git describe --dirty)"

if pip list | grep '^pxpx ' > /dev/null ; then
  # Uninstall px before doing install testing
  pip uninstall --yes pxpx
fi
pip install "${ENVDIR}"/pxpx-*.whl
px bash
test "$(px --version)" = "$(git describe --dirty)"
