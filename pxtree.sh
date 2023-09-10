#!/bin/bash

# Run ptop from current sources

tox -e package >/dev/null && ./px.pex --tree "$@"
