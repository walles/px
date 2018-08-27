#!/bin/bash

# For this script to work you need a working ~/.pypirc file:
# https://docs.python.org/3/distutils/packageindex.html#pypirc

set -o pipefail
set -e
set -x

cd "$(dirname "$0")"
find . -name 'px*.whl' -delete

# Build the release
./ci.sh

# Make a relelase virtualenv
ENVDIR="$(mktemp -d)"
function cleanup {
  rm -rf "${ENVDIR}"
}
trap cleanup EXIT

virtualenv "${ENVDIR}"
# shellcheck source=/dev/null
. "${ENVDIR}"/bin/activate

# Work around having an old version of OpenSSL
#
# https://github.com/pypa/twine/issues/273#issuecomment-334911815
pip install "ndg-httpsclient == 0.4.3"

pip install "twine == 1.9.1"

# Upload!
echo
# Note that we take the wheel file from one of our virtualenvs where
# it was built. When testing this for the 1.12 release, both wheel
# files (created with Python 2 or Python 3) were identical, so the
# choice of "python3" here is arbitrary.
twine upload --repository pypi .python3-env/pxpx-*-py2.py3-none-any.whl
