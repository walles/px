#!/bin/bash

set -euo pipefail

IMAGE="python:3.6-alpine"
COMMANDS="
set -ex

apk add sudo py3-tox shellcheck python2 bash git unzip lsof gcc python3-dev procps acct musl-dev

echo 'root    ALL=(ALL:ALL) ALL' > /etc/sudoers
adduser -u $(id -u) -g $(id -g) -D $USER

/usr/bin/sudo -u '#$(id -u)' -g '#$(id -g)' tox -p auto
"

docker run \
    -it --rm \
    --name tox-in-docker \
    -v "$(pwd):$(pwd)" \
    --workdir "$(pwd)" \
    "$IMAGE" \
    sh -c "$COMMANDS"
