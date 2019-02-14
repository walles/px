#!/bin/bash

# See: https://sipb.mit.edu/doc/safe-shell/
set -eu -o pipefail

# FIXME: Prompt user to set a good window size to begin with, 90x24 for example

# FIXME: Get these some other way on Linux?
# FIXME: One brew command for making these installed and up-to-date
for PACKAGE in asciinema giflossy imagemagick leiningen ; do
    brew install "$PACKAGE" || brew outdated "$PACKAGE" || brew upgrade "$PACKAGE"
done

# FIXME: Just "npm install asciicast2gif" after this PR has been merged:
# https://github.com/asciinema/asciicast2gif/pull/59
#
# And remove "leiningen" from the brew installs above
if [ ! -e ./node_modules/.bin/asciicast2gif ] ; then
    WORKDIR="node_modules/johan"
    mkdir -p "$WORKDIR"
    export WORKDIR
    (
        set -ex
        cd "$WORKDIR"
        git clone --recursive -b patch-1 git@github.com:walles/asciicast2gif.git
        cd asciicast2gif

        # From: https://github.com/asciinema/asciicast2gif#building-from-source
        npm install
        lein cljsbuild once main
        lein cljsbuild once page
    )
    npm install "$WORKDIR/asciicast2gif"
fi

# Make sure we have the latest build before recording
./ci.sh

# Record!
RECORDING=$(mktemp || mktemp -t ptop-ascii-recording.XXXXXXXX)
echo Recording into: "$RECORDING"...
asciinema rec --stdin --command="./px.pex --top" --overwrite "$RECORDING"
echo Recording saved into "$RECORDING"

# Convert the recording to a gif
./node_modules/.bin/asciicast2gif -S1 "$RECORDING" doc/ptop-screenshot-new.gif

rm "$RECORDING"

# Demo what we captured compared to what we had
for SCREENSHOT in doc/ptop-screenshot.gif doc/ptop-screenshot-new.gif; do
    echo
    ls -l "$SCREENSHOT"
    file "$SCREENSHOT"
    open -a 'Google Chrome' "$SCREENSHOT"
done
