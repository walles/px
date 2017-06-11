#!/usr/bin/python

"""px - ps and top for Human Beings
     https://github.com/walles/px

Usage:
  px
  px <filter>
  px <PID>
  px --top
  px --install
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
--install: Install /usr/local/bin/px and /usr/local/bin/ptop
--help: Print this help
--version: Print version information
"""

import sys
import pkg_resources

import os
import docopt
from . import px_top
from . import px_install
from . import px_process
from . import px_terminal
from . import px_processinfo


def install():
    # Find full path to self
    if not sys.argv:
        sys.stderr.write("ERROR: Can't find myself, can't install\n")
        return

    px_pex = sys.argv[0]
    if not px_pex.endswith(".pex"):
        sys.stderr.write("ERROR: Not running from .pex file, can't install\n")
        return

    px_install.install(px_pex, "/usr/local/bin/px")
    px_install.install(px_pex, "/usr/local/bin/ptop")


def get_version():
    return pkg_resources.get_distribution("pxpx").version


def main():
    if len(sys.argv) == 1 and os.path.basename(sys.argv[0]).endswith("top"):
        sys.argv.append("--top")

    args = docopt.docopt(__doc__, version=get_version())

    if args['--install']:
        install()
        return

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
    main()
