#!/usr/bin/python

import os

import px_process


def get_terminal_window_width():
    result = os.popen('stty size', 'r').read().split()
    if len(result) >= 2:
        rows, columns = result
    else:
        columns = 12345678  # Really wide to disable truncation
    return int(columns)


def print_procs(procs):
    # Compute widest width for pid, user, cpu and memory usage columns
    pid_width = 0
    user_width = 0
    cpu_width = 0
    mem_width = 0
    for proc in procs:
        pid_width = max(pid_width, len(str(proc.pid)))
        user_width = max(user_width, len(proc.user))
        cpu_width = max(cpu_width, len(proc.cpu_time_s))
        mem_width = max(mem_width, len(proc.memory_percent_s))

    format = (
        '{:>' + str(pid_width) +
        '} {:' + str(user_width) +
        '} {:>' + str(cpu_width) +
        '} {:>' + str(mem_width) + '} {}')

    # FIXME: Print process list using the computed column widths
    terminal_window_width = get_terminal_window_width()
    for proc in procs:
        line = format.format(
            proc.pid, proc.user, proc.cpu_time_s, proc.memory_percent_s,
            proc.cmdline)
        print(line[0:terminal_window_width])


procs = px_process.get_all()

# Print the most interesting processes last; there are lots of processes and
# the end of the list is where your eyes will be when you get the prompt back.
print_procs(sorted(procs, key=lambda proc: proc.score))
