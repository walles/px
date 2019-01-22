#!/bin/bash

# See: https://sipb.mit.edu/doc/safe-shell/
set -ef -o pipefail

# FIXME: Prompt user to set a good window size to begin with

# FIXME: Install some other way on Linux? "pip3 install"?
brew install asciinema

# FIXME: ./ci.sh
RECORDING=$(mktemp || mktemp -t ptop-ascii-recording.XXXXXXXX)
echo Recording into: $RECORDING...
asciinema rec --stdin --command="./px.pex --top" --overwrite $RECORDING
echo Recording saved into $RECORDING

# FIXME: Use asciicast2gif to convert the recording to a gif
