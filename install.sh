#!/bin/bash -e
#
# Download and install the latest release

# Give up on any failure
set -e
set -o pipefail

REPO="walles/px"
PXPREFIX=${PXPREFIX:-/usr/local/bin}

# Get the download URL for the latest release
TEMPFILE=$(mktemp || mktemp -t px-install-releasesjson.XXXXXXXX)
curl -s https://api.github.com/repos/${REPO}/releases >"${TEMPFILE}"
if grep "API rate limit exceeded" "${TEMPFILE}" >/dev/null; then
  cat "${TEMPFILE}" >&2
  exit 1
fi

URL=$(
  grep browser_download_url "${TEMPFILE}" |
    cut -d '"' -f 4 |
    head -n 1
)
rm "${TEMPFILE}"

echo "Downloading the latest release..."
echo "  ${URL}"
TEMPFILE=$(mktemp || mktemp -t px-install.XXXXXXXX)
curl -L -s "${URL}" >"${TEMPFILE}"
chmod a+x "${TEMPFILE}"

echo "Installing the latest release..."
echo
echo "sudo install px.pex ${PXPREFIX}/px"
sudo install "${TEMPFILE}" "${PXPREFIX}/px"
echo "sudo ln px ${PXPREFIX}/ptop"
sudo ln -sf px "${PXPREFIX}/ptop"
echo "sudo ln px ${PXPREFIX}/pxtree"
sudo ln -sf px "${PXPREFIX}/pxtree"

rm -f "${TEMPFILE}"

echo
echo "Installation done, now run one or all of:"
echo "  ptop"
echo "  pxtree"
echo "  px"
