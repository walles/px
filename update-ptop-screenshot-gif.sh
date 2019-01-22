#!/bin/bash

# See: https://sipb.mit.edu/doc/safe-shell/
set -ef -o pipefail

# FIXME: Prompt user to set a good window size to begin with

# FIXME: Get these some other way on Linux?
brew install asciinema giflossy imagemagick

npm install asciicast2gif

# Make sure we have the latest build before recording
./ci.sh

# Record!
RECORDING=$(mktemp || mktemp -t ptop-ascii-recording.XXXXXXXX)
echo Recording into: $RECORDING...
asciinema rec --stdin --command="./px.pex --top" --overwrite $RECORDING
echo Recording saved into $RECORDING

# Convert the recording to a gif
./node_modules/.bin/asciicast2gif $RECORDING doc/ptop-screenshot.gif

rm $RECORDING

# Demo what we captured
open -a 'Google Chrome' doc/ptop-screenshot.gif
