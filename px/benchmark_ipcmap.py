#!/usr/bin/env python

"""Benchmark loading the output of "lsof -F fnaptd0" from a big system

Usage:
  benchmark_ipcmap.py <FILE>

FILE is a file containing the output of "lsof -F fnaptd0".

This program will parse that output and make an IPC map of the process that has
the highest number of entries in that file.
"""

import time

import docopt
import testutils
import px_file


def get_most_common_pid(files):
    counts = {}
    for file in files:
        pid = file.pid
        if pid not in counts:
            counts[pid] = 0
        counts[pid] += 1
    return sorted(counts.keys(), key=lambda pid: counts[pid])[-1]


def main(args):
    t0 = time.time()
    files = None
    with open(args['<FILE>'], "r") as lsof_output:
        files = px_file.lsof_to_files(lsof_output.read())
    t1 = time.time()
    dt = t1 - t0
    print("Parsing lsof output: {}s".format(dt))

    pid = get_most_common_pid(files)
    print("Most popular PID: {}".format(pid))

    t0 = time.time()
    testutils.create_ipc_map(pid, files)
    t1 = time.time()
    dt = t1 - t0
    print("Creating PID {} IPC map: {}s".format(pid, dt))


if __name__ == "__main__":
    main(docopt.docopt(__doc__))
