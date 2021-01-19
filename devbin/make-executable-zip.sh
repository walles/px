#!/usr/bin/env bash

set -e -o pipefail

MYDIR="$(cd "$(dirname "$0")"; pwd)"
ROOTDIR="$MYDIR/.."
ZIPFILE="$ROOTDIR/px.pex"
export ZIPOPT="-9 -q"

ENVDIR="$(mktemp -d)"
rmdir "$ENVDIR"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$ENVDIR" "$WORKDIR" "$ZIPFILE.tmp"' EXIT

# Create a virtualenv in a temporary location
virtualenv -p python "$ENVDIR"

# shellcheck source=/dev/null
. "$ENVDIR/bin/activate"
pip install -r "$ROOTDIR/requirements.txt"

# Set up file structure in our temporary directory
echo 'import px.px; px.px.main()' > "$WORKDIR/__main__.py"

# The main attraction!
cp -a "$ROOTDIR/px" "$WORKDIR/"

# Dependencies, must match list in requirements.txt
cp -a "$ENVDIR/lib/python3.9/site-packages/dateutil" "$WORKDIR/"
cp -a "$ENVDIR/lib/python3.9/site-packages/six.py" "$WORKDIR/"

# Tidy up a bit
find "$WORKDIR" -name '*.pyc' -delete

# Create zip file
cd "$WORKDIR"
zip -r "$ZIPFILE.tmp" ./*

# Add Python shebang, from: https://stackoverflow.com/a/10587688/473672
(echo '#!/usr/bin/env python'; cat "$ZIPFILE.tmp") > "$ZIPFILE"

chmod a+x "$ZIPFILE"
