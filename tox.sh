#!/bin/bash -e

# Run this for local testing
tox --skip-missing-interpreters -p auto "$@"
