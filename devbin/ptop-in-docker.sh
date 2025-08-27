#!/bin/bash

set -euo pipefail

DOCKERFILE="
FROM python:3.9-alpine

RUN apk add sudo py3-tox shellcheck bash git unzip lsof gcc python3-dev procps acct musl-dev zip
RUN echo 'root    ALL=(ALL:ALL) ALL' > /etc/sudoers
RUN adduser -u $(id -u) -g $(id -g) -D $USER
"

echo "$DOCKERFILE" | docker build --tag=ptop-in-docker -

# NOTE: The actual ptop invocation ignores command line parameters to this
# script, fix if needed.
docker run \
    -it --rm \
    --name ptop-in-docker \
    -v "$(pwd):$(pwd)" \
    --workdir "$(pwd)" \
    tox-in-docker \
    sh -c "/usr/bin/sudo -u '#$(id -u)' -g '#$(id -g)' ./ptop.sh"
