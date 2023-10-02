#!/bin/bash

WORKDIR="$(mktemp -d)"
function installer-cleanup {
  rm -rf "${WORKDIR}"
}
trap installer-cleanup EXIT

# Create a fake no-op sudo...
SUDO=${WORKDIR}/sudo
echo '#!/bin/bash' >"${SUDO}"
echo '"$@"' >>"${SUDO}"
chmod a+x "${SUDO}"

# ... and a fake curl...
CURL="${WORKDIR}/curl"
echo '#!/bin/bash' >"${CURL}"
echo 'cat tests/api.github.com_releases.json' >>"${CURL}"
chmod a+x "${CURL}"

# ... and put both first in the PATH
export PATH=${WORKDIR}:$PATH

cat <<EOF
#
#  Testing happy-path install...
#
EOF
PXPREFIX=${WORKDIR} bash ./install.sh
test -x "${WORKDIR}/px"
test -x "${WORKDIR}/ptop"
test -x "${WORKDIR}/pxtree"

#
# Make curl fail
#
echo '#!/bin/bash' >"${CURL}"
echo 'cat tests/api.github.com_releases-ratelimit.json' >>"${CURL}"
chmod a+x "${CURL}"

# Remove binaries so that we can verify they don't get installed
rm "${WORKDIR}/px"
rm "${WORKDIR}/ptop"
rm "${WORKDIR}/pxtree"

cat <<EOF
#
#  Testing rate-limited by Github install...
#
EOF
# Installation should fail with an error code, that's why we're "!"ing it
! PXPREFIX=${WORKDIR} bash ./install.sh 2>"${WORKDIR}/message.txt"
# The installer should just have printed the error message on stderr
diff -u "${WORKDIR}/message.txt" "tests/api.github.com_releases-ratelimit.json"
! test -e "${WORKDIR}/px"
! test -e "${WORKDIR}/ptop"
! test -e "${WORKDIR}/pxtree"
