#!/bin/bash -e
#
# Download and install the latest release

# Give up on any failure
set -e
set -o pipefail

REPO="walles/px"

# This is the download URL for the latest release
URL=$(curl -s https://api.github.com/repos/$REPO/releases \
  | grep browser_download_url \
  | head -n 1 \
  | cut -d '"' -f 4)

echo "Downloading the latest release..."
echo "  $URL"
TEMPFILE=$(mktemp)
curl -L -s "$URL" > $TEMPFILE
chmod a+x $TEMPFILE

echo "Installing the latest release..."
echo
echo "sudo install px.pex /usr/local/bin/px"
sudo install $TEMPFILE /usr/local/bin/px
echo "sudo install px.pex /usr/local/bin/ptop"
sudo install $TEMPFILE /usr/local/bin/ptop

rm -f $TEMPFILE

echo
echo "Installation done, now run one or both of:"
echo "  px"
echo "  ptop"
