import sys

import os
from . import px_process


def get_window_size():
    """
    Return the terminal window size as tuple (rows, columns) if available, or
    None if not.
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

    rows = int(rows)
    if rows < 1:
        # Don't know if this actually happens, we just do it for symmetry with
        # the columns check above
        return None

    return (rows, columns)


def to_screen_lines(procs, columns):
    """
    Returns an array of lines that can be printed to screen. Each line is at
    most columns wide.

    If columns is None, line lengths are unbounded.
    """
    class Headings(px_process.PxProcess):
        def __init__(self):
            pass

    headings = Headings()
    headings.pid = "PID"
    headings.command = "COMMAND"
    headings.username = "USERNAME"
    headings.cpu_time_s = "CPU"
    headings.memory_percent_s = "RAM"
    headings.cmdline = "COMMANDLINE"
    procs = [headings] + procs

    # Compute widest width for pid, command, user, cpu and memory usage columns
    pid_width = 0
    command_width = 0
    username_width = 0
    cpu_width = 0
    mem_width = 0
    for proc in procs:
        pid_width = max(pid_width, len(str(proc.pid)))
        command_width = max(command_width, len(proc.command))
        username_width = max(username_width, len(proc.username))
        cpu_width = max(cpu_width, len(proc.cpu_time_s))
        mem_width = max(mem_width, len(proc.memory_percent_s))

    format = (
        '{:>' + str(pid_width) +
        '} {:' + str(command_width) +
        '} {:' + str(username_width) +
        '} {:>' + str(cpu_width) +
        '} {:>' + str(mem_width) + '} {}')

    # Print process list using the computed column widths
    lines = []
    for proc in procs:
        line = format.format(
            proc.pid, proc.command, proc.username,
            proc.cpu_time_s, proc.memory_percent_s,
            proc.cmdline)
        lines.append(line[0:columns])

    return lines


def inverse_video(string):
    CSI = "\x1b["

    return CSI + "7m" + string + CSI + "0m"


def get_string_of_length(string, length):
    if not length:
        return string

    if len(string) < length:
        return string + (length - len(string)) * ' '

    if len(string) > length:
        return string[0:length]

    return string
