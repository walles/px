#!/usr/bin/env python3

"""Benchmark listing all processes

Usage:
  benchmark_proc_get_all.py
"""

import os
import sys
import time


MYDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(MYDIR, ".."))

from px import px_process  # noqa: E402

LAPS = 20


def main():
    t0 = time.time()
    for _ in range(LAPS):
        px_process.get_all()
    t1 = time.time()
    dt_seconds = t1 - t0

    print(f"Getting all processes takes {1000 * dt_seconds / LAPS:.0f}ms")


if __name__ == "__main__":
    main()
