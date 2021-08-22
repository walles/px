#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Benchmark listing all processes

Usage:
  benchmark_proc_get_all.py
"""

import os

MYDIR = os.path.dirname(os.path.abspath(__file__))

import sys

sys.path.insert(0, os.path.join(MYDIR, ".."))

import time

from px import px_process

LAPS = 20


def main():
    t0 = time.time()
    for iteration in range(LAPS):
        px_process.get_all()
    t1 = time.time()
    dt_seconds = t1 - t0

    print("Getting all processes takes {:.0f}ms".format(1000 * dt_seconds / LAPS))


if __name__ == "__main__":
    main()
