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
    columns = None
    window_size = px_terminal.get_window_size()
    if window_size is not None:
        columns = window_size[1]
    lines = px_terminal.to_screen_lines(px_process.order_best_last(procs), columns)
    print("\n".join(lines))


if __name__ == "__main__":
    main(docopt.docopt(__doc__, version=get_version()))
