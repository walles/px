#!/bin/bash

# Run pxtree from current sources

PYTHONPATH=px:$(echo env/lib/python*/site-packages) python3 -m px.px --tree "$@"
