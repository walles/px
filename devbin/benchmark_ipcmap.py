#!/usr/bin/env python3

"""Benchmark loading the output of "lsof -F fnaptd0i" from a big system

Usage:
  benchmark_ipcmap.py <FILE>

FILE is a file containing the output of "lsof -F fnaptd0i".

This program will parse that output and make an IPC map of the process that has
the highest number of entries in that file.
"""

import os
import sys
import time

from typing import MutableMapping


MYDIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(MYDIR, ".."))

from tests import testutils
from px import px_file


# For how long should we do the benchmarking run (in seconds)
DURATION_S = 30


def get_most_common_pid(files):
    counts: MutableMapping[int, int] = {}
    for file in files:
        pid = file.pid
        if pid not in counts:
            counts[pid] = 0
        counts[pid] += 1
    return sorted(counts.keys(), key=lambda pid: counts[pid])[-1]


def get_timings(file, pid):
    """
    Loads file and creates an IPC map for PID.

    Returns timings in a tuple (load, mapping) in seconds.
    """
    t0 = time.time()
    files = None
    with open(file, encoding="utf-8") as lsof_output:
        files = px_file.lsof_to_files(lsof_output.read())
    t1 = time.time()
    dt_load = t1 - t0

    t0 = time.time()
    testutils.create_ipc_map(pid, files)
    t1 = time.time()
    dt_mapping = t1 - t0

    return (dt_load, dt_mapping)


def print_statistics(name, values):
    lowest = min(values)
    highest = max(values)
    middle = (lowest + highest) / 2
    radius = (highest - lowest) / 2
    print(f"{name} is {middle:.2f}s±{radius:.2f}s")


def main(lsof_file):
    print("Finding most popular PID...")
    files = None
    with open(lsof_file, encoding="utf-8") as lsof_output:
        files = px_file.lsof_to_files(lsof_output.read())
    pid = get_most_common_pid(files)
    print(f"Most popular PID: {pid}")

    end = time.time() + DURATION_S
    lap_number = 0
    load_times = []
    mapping_times = []
    total_times = []
    while time.time() < end:
        lap_number += 1
        print(f"Lap {lap_number}, {end - time.time():.0f}s left...")
        load_time, mapping_time = get_timings(lsof_file, pid)
        load_times.append(load_time)
        mapping_times.append(mapping_time)
        total_times.append(load_time + mapping_time)

    print_statistics("Loading time", load_times)
    print_statistics("Mapping time", mapping_times)
    print_statistics("  Total time", total_times)


if __name__ == "__main__":
    main(sys.argv[1])
