#!/bin/bash -e
#
# Download and install the latest release
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
echo "sudo px --install"
sudo $TEMPFILE --install

rm -f $TEMPFILE

echo
echo "Installation done, now run one or both of:"
echo "  px"
echo "  ptop"
