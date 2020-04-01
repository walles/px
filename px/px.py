#!/usr/bin/python

"""px - ps and top for Human Beings
     https://github.com/walles/px

Usage:
  px [--debug]
  px [--debug] <filter>
  px [--debug] <PID>
  px [--debug] --top
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
--debug: Print debug logs (if any) after running
--install: Install /usr/local/bin/px and /usr/local/bin/ptop
--help: Print this help
--version: Print version information
"""

import platform
import logging
import six
import sys
import os

from . import px_install
from . import px_process
from . import px_terminal
from . import px_processinfo


ERROR_REPORTING_HEADER = """
---

Problems detected, please send this text to one of:
* https://github.com/walles/px/issues/new
* johan.walles@gmail.com
"""


def install(argv):
    # Find full path to self
    if not argv:
        sys.stderr.write("ERROR: Can't find myself, can't install\n")
        return

    px_pex = argv[0]
    if not px_pex.endswith(".pex"):
        sys.stderr.write("ERROR: Not running from .pex file, can't install\n")
        return

    px_install.install(px_pex, "/usr/local/bin/px")
    px_install.install(px_pex, "/usr/local/bin/ptop")


# This is the setup.py entry point
def main():
    _main(sys.argv)


def configureLogging(loglevel, stringIO):
    # type: (int, six.StringIO) -> None

    # This method inspired by: https://stackoverflow.com/a/9534960/473672

    rootLogger = logging.getLogger()
    rootLogger.setLevel(loglevel)

    handlers = []
    for handler in rootLogger.handlers:
        handlers.append(handler)
    for handler in handlers:
        rootLogger.removeHandler(handler)

    handler = logging.StreamHandler(stringIO)
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S%Z')
    handler.setFormatter(formatter)

    rootLogger.addHandler(handler)


def handleLogMessages(messages):
    if not messages:
        return

    sys.stderr.write(ERROR_REPORTING_HEADER)
    sys.stderr.write("\n")
    sys.stderr.write("Python version: " + sys.version + "\n")
    sys.stderr.write("\n")
    sys.stderr.write("Platform info: " + platform.platform() + "\n")
    sys.stderr.write("\n")
    sys.stderr.write(messages)
    sys.stderr.write("\n")
    sys.exit(1)


def _main(argv):
    loglevel = logging.ERROR
    while '--debug' in argv:
        argv.remove('--debug')
        loglevel = logging.DEBUG

    if len(argv) == 1 and os.path.basename(argv[0]).endswith("top"):
        argv.append("--top")

    if len(argv) == 1:
        # This is an empty filterstring
        argv.append("")

    if len(argv) > 2:
        sys.stderr.write("ERROR: Expected zero or one argument but got more\n\n")
        print(__doc__)
        sys.exit(1)

    arg = argv[1]

    if arg == '--install':
        install(argv)
        return

    stringIO = six.StringIO()
    configureLogging(loglevel, stringIO)

    if arg == '--top':
        # Pulling px_top in on demand like this improves test result caching
        from . import px_top
        px_top.top()
        handleLogMessages(stringIO.getvalue())
        return

    if arg == '--help':
        print(__doc__)
        return

    if arg == '--version':
        # If this fails, run "tox.sh" once and the "version.py" file will be created for you.
        #
        # NOTE: If we "import version" at the top of this file, we will depend on it even if
        # we don't use it. And this will make test avoidance fail to avoid px.py tests every
        # time you make a new commit (because committing recreates version.py).
        from . import version

        print(version.VERSION)
        return

    try:
        pid = int(arg)
        px_processinfo.print_pid_info(sys.stdout.fileno(), pid)
        handleLogMessages(stringIO.getvalue())
        return
    except ValueError:
        # It's a search filter and not a PID, keep moving
        pass

    procs = filter(lambda p: p.match(arg), px_process.get_all())

    # Print the most interesting processes last; there are lots of processes and
    # the end of the list is where your eyes will be when you get the prompt back.
    columns = None
    window_size = px_terminal.get_window_size()
    if window_size is not None:
        columns = window_size[1]
    lines = px_terminal.to_screen_lines(px_process.order_best_last(procs), columns, None, None)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
