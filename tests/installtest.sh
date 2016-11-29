#!/bin/bash

WORKDIR="$(mktemp -d)"
function installer-cleanup {
  rm -rf "${WORKDIR}"
}
trap installer-cleanup EXIT

# Create a fake no-op sudo...
SUDO=${WORKDIR}/sudo
echo '#!/bin/bash' > ${SUDO}
echo '"$@"' >> ${SUDO}
chmod a+x ${SUDO}

# ... and a fake curl...
CURL=${WORKDIR}/curl
echo '#!/bin/bash' > ${CURL}
echo 'cat tests/api.github.com_releases.json' >> ${CURL}
chmod a+x ${CURL}

# ... and put both first in the PATH
export PATH=${WORKDIR}:$PATH

PXPREFIX=${WORKDIR} bash -x ./install.sh
test -x ${WORKDIR}/px
test -x ${WORKDIR}/ptop
