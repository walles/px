#!/usr/bin/python

"""px - A Cross Functional Process Explorer

Usage:
  px
  px <filter>
  px <PID>
  px --help
  px --version

In the base case, px list all processes much like ps, but with the most
interesting processes last. A process is considered interesting if it has high
memory usage or has used lots of CPU.

If the optional filter parameter is specified, processes will be shown if:
* The filter matches the user name of the process
* The filter matches a substring of the command line

If the optional PID parameter is specified, you'll get detailed information
about that particular PID.

--help: Print this help
--version: Print version information
"""

import sys
import zipfile

import os
import docopt
import px_process
import px_processinfo


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


def get_version():
    """Extract version string from PEX-INFO file"""
    my_pex_name = os.path.dirname(__file__)
    zip = zipfile.ZipFile(my_pex_name)
    pex_info_string = str(zip.read("PEX-INFO"))
    pex_info_string_python = pex_info_string.replace("false", "False").replace("true", "True")
    pex_info = eval(pex_info_string_python)
    return pex_info['build_properties']['tag']


def main(args):
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
