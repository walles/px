#!/bin/bash

set -o pipefail
set -e
cd "$(dirname "$0")"

if ! [ -f ~/.pypirc ] ; then
  echo "ERROR: For this script to work you need a working ~/.pypirc file:"
  echo "       https://docs.python.org/3/distutils/packageindex.html#pypirc"
  exit 1
fi

# Ask user to consider updating the README.rst Output section.
cat << EOM
Please consider updating the Output section of README.rst before releasing.

This includes the ptop screenshot, scale your window to 90x24 before shooting it.

Answer yes at this prompt to verify that the Output section is complete.
EOM

read -r -p "Output section complete: " MAYBE_YES
if [ "$MAYBE_YES" != "yes" ] ; then
  echo
  echo "Please update the Output section of README.rst and try this script again."
  exit 0
fi

# Verify that we're on the python branch
if [ "$(git rev-parse --abbrev-ref HEAD)" != "python" ] ; then
  echo "ERROR: Releases can be done from the 'python' branch only"
  exit 1
fi

# Verify there are no outstanding changes
if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: There are outstanding changes, make sure your working directory is clean before releasing"
  echo
  git status
  exit 1
fi

# List changes since last release
echo
echo "List of changes since last release:"
git log --color --format="format:%Cgreen%s%Creset (%ad)%n%b" --first-parent "$(git describe --abbrev=0)..HEAD" | cat

echo
echo "=="
echo "Last version number was $(git describe --abbrev=0), enter new version number."
read -r -p "New version number: " NEW_VERSION_NUMBER

# Validate new version number
if [ -z "$NEW_VERSION_NUMBER" ] ; then
  echo "Empty version number, never mind"
  exit 0
fi

echo Please enter "$NEW_VERSION_NUMBER" again:
read -r -p "  Validate version: " VALIDATE_VERSION_NUMBER

if [ "$NEW_VERSION_NUMBER" != "$VALIDATE_VERSION_NUMBER" ] ; then
  echo "Version numbers mismatch, never mind"
  exit 1
fi

# Get release message from user
cat << EOM

==
You will now get to compose the release description for Github,
write something nice! And remember that the first line is the
subject line for the release.

EOM
read -r -p "Press ENTER when ready: "

git tag --annotate "$NEW_VERSION_NUMBER"

# Lots of automation from here on, be verbose for troubleshooting purposes
set -x

cd "$(dirname "$0")"
find . -name 'px*.whl' -delete

# Build the release
tox

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

# Mark new release on Github
git push --tags

cat << EOM

==
Now, go to the Releases page on GitHub...

https://github.com/walles/px/releases

... and click your new release, click the "Edit tag" button, then attach
your "px.pex" file that was just built to the release.

After uploading that file, press "Publish release".

EOM

read -r -p "Press ENTER when done: "

echo
echo "=="
echo "Your release should now be available on Github and at https://pypi.python.org/pypi/pxpx"
