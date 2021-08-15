#!/bin/bash

set -o pipefail
set -e
cd "$(dirname "$0")/.."

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

# If not, we'll for some reason get 0.0.0 versioned files in dist2/ and dist3/,
# which messes up out Pypi publishing.
echo "Version number must be on 1.2.3 format for the buildscripts to work."

read -r -p "New version number: " NEW_VERSION_NUMBER

# Validate new version number
if [ -z "$NEW_VERSION_NUMBER" ] ; then
  echo "Empty version number, never mind"
  exit 0
fi

if ! echo "$NEW_VERSION_NUMBER" | grep -E '^[0-9]+[.][0-9]+[.][0-9]+$' ; then
  echo "Version number not in 1.2.3 format, never mind"
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
# Note that we take the wheel file from one of our dist directories where it was
# built. When testing this for the 1.0.33 release, both wheel files (created
# with Python 2 or Python 3) had identical contents when unzipped, so the choice
# of "dist3" here is arbitrary.
twine upload --repository pypi dist3/pxpx-*-py2.py3-none-any.whl

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

cat << EOM

==
Now, make a PR for bumping the homebrew packaging version to $NEW_VERSION_NUMBER:

  brew bump-formula-pr --strict px --tag=$NEW_VERSION_NUMBER --revision=$(git rev-parse HEAD)

EOM

# Ref: https://github.com/Homebrew/homebrew-core/actions/runs/1132207320
read -r -p "Press ENTER when the PR CI has passed, this took 22 minutes for release 1.5.1: "

cat << EOM

==
Your release should now be visible here:
* https://github.com/walles/px/releases/latest
* https://formulae.brew.sh/formula/px
* https://pypi.python.org/pypi/pxpx
EOM
