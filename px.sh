#!/bin/bash

# Run px from current sources

tox -e package > /dev/null && ./px.pex "$@"
