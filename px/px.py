#!/usr/bin/python

import os
import psutil

import px_process


def get_terminal_window_width():
    result = os.popen('stty size', 'r').read().split()
    if len(result) >= 2:
        rows, columns = result
    else:
        columns = 12345678  # Really wide to disable truncation
    return int(columns)

# List all processes, and print for each process: PID, owner,
# memory usage (in %), used CPU time and full command line
#
# FIXME: Sort printed list by (memory usage) * (used CPU time)
terminal_window_width = get_terminal_window_width()
print terminal_window_width
for proc in psutil.process_iter():
    pinfo = px_process.PxProcess(proc)

    line = "{:>6} {:9} {:>9} {:>4} {}".format(
        pinfo.pid, pinfo.user, pinfo.cpu_time_s, pinfo.memory_percent_s,
        pinfo.cmdline)
    print line[0:terminal_window_width]
