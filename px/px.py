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

procs = []
for proc in psutil.process_iter():
    procs.append(px_process.PxProcess(proc))

terminal_window_width = get_terminal_window_width()
for proc in sorted(procs, key=lambda proc: -proc.score):
    line = "{:>6} {:9} {:>9} {:>4} {}".format(
        proc.pid, proc.user, proc.cpu_time_s, proc.memory_percent_s,
        proc.cmdline)
    print line[0:terminal_window_width]
