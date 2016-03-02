#!/usr/bin/python

import sys

import os
import px_process


def get_terminal_window_width():
    """
    Return the width of the terminal if available, or None if not.
    """

    if not sys.stdout.isatty():
        # We shouldn't truncate lines when piping
        return None

    result = os.popen('stty size', 'r').read().split()
    if len(result) < 2:
        # Getting the terminal window width failed, don't truncate
        return None

    rows, columns = result
    columns = int(columns)
    if columns < 1:
        # This seems to happen during OS X CI runs:
        # https://travis-ci.org/walles/px/jobs/113134994
        return None

    return columns


def print_procs(procs):
    # Compute widest width for pid, user, cpu and memory usage columns
    pid_width = 0
    username_width = 0
    cpu_width = 0
    mem_width = 0
    for proc in procs:
        pid_width = max(pid_width, len(str(proc.pid)))
        username_width = max(username_width, len(proc.username))
        cpu_width = max(cpu_width, len(proc.cpu_time_s))
        mem_width = max(mem_width, len(proc.memory_percent_s))

    format = (
        '{:>' + str(pid_width) +
        '} {:' + str(username_width) +
        '} {:>' + str(cpu_width) +
        '} {:>' + str(mem_width) + '} {}')

    # Print process list using the computed column widths
    terminal_window_width = get_terminal_window_width()
    for proc in procs:
        line = format.format(
            proc.pid, proc.username, proc.cpu_time_s, proc.memory_percent_s,
            proc.cmdline)
        print(line[0:terminal_window_width])


def main():
    procs = px_process.get_all()

    # Print the most interesting processes last; there are lots of processes and
    # the end of the list is where your eyes will be when you get the prompt back.
    print_procs(px_process.order_best_last(procs))


if __name__ == "__main__":
    main()
