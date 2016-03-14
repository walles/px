#!/usr/bin/python

"""px - A Cross Functional Process Explorer
     https://github.com/walles/px

Usage:
  px
  px <filter>
  px <PID>
  px --top
  px --help
  px --version

In the base case, px list all processes much like ps, but with the most
interesting processes last. A process is considered interesting if it has high
memory usage, has used lots of CPU or has been started recently.

If the optional filter parameter is specified, processes will be shown if:
* The filter matches the user name of the process
* The filter matches a substring of the command line

If the optional PID parameter is specified, you'll get detailed information
about that particular PID.

In --top mode, a new process list is shown every second. The most interesting
processes are on top. In this mode, CPU times are counted from when you first
invoked px, rather than from when each process started. This gives you a picture
of which processes are most active right now.

--top: Show a continuously refreshed process list
--help: Print this help
--version: Print version information
"""

import json
import zipfile

import os
import docopt
import px_top
import px_process
import px_terminal
import px_processinfo


def print_procs(procs):
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
    terminal_window_size = px_terminal.get_window_size()
    columns = None
    if terminal_window_size:
        columns = terminal_window_size[1]
    for proc in procs:
        line = format.format(
            proc.pid, proc.command, proc.username,
            proc.cpu_time_s, proc.memory_percent_s,
            proc.cmdline)
        print(line[0:columns])


def get_version():
    """Extract version string from PEX-INFO file"""
    my_pex_name = os.path.dirname(__file__)
    zip = zipfile.ZipFile(my_pex_name)
    with zip.open("PEX-INFO") as pex_info:
        return json.load(pex_info)['build_properties']['tag']


def main(args):
    if args['--top']:
        px_top.top()
        return

    filterstring = args['<filter>']
    if filterstring:
        try:
            pid = int(filterstring)
            px_processinfo.print_process_info(pid)
            return
        except ValueError:
            # It's a search filter and not a PID, keep moving
            pass

    procs = px_process.get_all()
    procs = filter(lambda p: p.match(filterstring), procs)

    # Print the most interesting processes last; there are lots of processes and
    # the end of the list is where your eyes will be when you get the prompt back.
    print_procs(px_process.order_best_last(procs))


if __name__ == "__main__":
    main(docopt.docopt(__doc__, version=get_version()))
