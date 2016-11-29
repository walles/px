#!/bin/bash -e
#
# Download and install the latest release

# Give up on any failure
set -e
set -o pipefail

REPO="walles/px"
PXPREFIX=${PXPREFIX:-/usr/local/bin}

# This is the download URL for the latest release
URL=$(curl -s https://api.github.com/repos/$REPO/releases \
  | grep browser_download_url \
  | cut -d '"' -f 4 \
  | head -n 1)

echo "Downloading the latest release..."
echo "  $URL"
TEMPFILE=$(mktemp || mktemp -t px-install.XXXXXXXX)
curl -L -s "$URL" > $TEMPFILE
chmod a+x $TEMPFILE

echo "Installing the latest release..."
echo
echo "sudo install px.pex /usr/local/bin/px"
sudo install $TEMPFILE ${PXPREFIX}/px
echo "sudo install px.pex /usr/local/bin/ptop"
sudo install $TEMPFILE ${PXPREFIX}/ptop

rm -f $TEMPFILE

echo
echo "Installation done, now run one or both of:"
echo "  px"
echo "  ptop"
