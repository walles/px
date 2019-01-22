#!/bin/bash

# See: https://sipb.mit.edu/doc/safe-shell/
set -eu -o pipefail

# FIXME: Prompt user to set a good window size to begin with, 90x24 for example

# FIXME: Get these some other way on Linux?
brew install asciinema giflossy imagemagick

npm install asciicast2gif

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
for SCREENSHOT in doc/ptop-screenshot*.gif; do
    echo
    ls -l "$SCREENSHOT"
    file "$SCREENSHOT"
    open -a 'Google Chrome' "$SCREENSHOT"
done
