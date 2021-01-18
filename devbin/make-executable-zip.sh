#!/usr/bin/env bash

set -e -o pipefail

MYDIR="$(cd "$(dirname "$0")"; pwd)"
ROOTDIR="$MYDIR/.."
ZIPFILE="$ROOTDIR/px.exe"
export ZIPOPT="-9 -q"

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR" "$ZIPFILE.tmp"' EXIT

# Set up file structure in our temporary directory
cp "$MYDIR/executable-zip-bootstrap.py" "$WORKDIR/__main__.py"

# The main attraction!
cp -a "$ROOTDIR/px" "$WORKDIR/"

# FIXME: Where should we really get these from?
cp -a "$ROOTDIR/env/lib/python3.9/site-packages/dateutil" "$WORKDIR/"
cp -a "$ROOTDIR/env/lib/python3.9/site-packages/six.py" "$WORKDIR/"

# Tidy up a bit
find "$WORKDIR" -name '*.pyc' -delete

# Create zip file
cd "$WORKDIR"
zip -r "$ZIPFILE.tmp" ./*

# Add Python shebang, from: https://stackoverflow.com/a/10587688/473672
(echo '#!/usr/bin/env python'; cat "$ZIPFILE.tmp") > "$ZIPFILE"

chmod a+x "$ZIPFILE"
