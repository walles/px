#!/usr/bin/python

"""px - ps and top for Human Beings
     https://github.com/walles/px

Usage:
  px [--debug] [--sort=cpupercent] [--no-username] [filter string]
  px [--debug] [--no-pager] [--color] <PID>
  px [--debug] --top [filter string]
  px --install
  px --help
  px --version

In the base case, px list all processes much like ps, but with the most
interesting processes last. A process is considered interesting if it has high
memory usage, has used lots of CPU or has been started recently.

If the optional filter string parameter is specified, processes will be shown if:
* The filter matches the user name of the process
* The filter matches a substring of the command line

If the optional PID parameter is specified, you'll get detailed information
about that particular PID.

In --top mode, a new process list is shown every second. The most CPU heavy
processes are on top. In this mode, CPU times are counted from when you first
invoked px, rather than from when each process started. This gives you a picture
of which processes are most active right now.

--top: Show a continuously refreshed process list
--debug: Print debug logs (if any) after running
--install: Install /usr/local/bin/px and /usr/local/bin/ptop
--no-pager: Print PID info to stdout rather than to a pager
--sort=cpupercent: Order processes by CPU percentage only
--no-username: Don't show the username column in px output
--color: Force color output even when piping
--help: Print this help
--version: Print version information
"""

import operator
import platform
import logging
import sys
import io
import os

from . import px_pager
from . import px_install
from . import px_process
from . import px_terminal
from . import px_processinfo

from typing import Optional, List


ERROR_REPORTING_HEADER = """
---

Problems detected, please send this text to one of:
* https://github.com/walles/px/issues/new
* johan.walles@gmail.com
"""


def install(argv: List[str]) -> None:
    """Find full path to self"""
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
    argv = list(sys.argv)

    loglevel = logging.ERROR
    while "--debug" in argv:
        argv.remove("--debug")
        loglevel = logging.DEBUG

    stringIO = io.StringIO()
    configureLogging(loglevel, stringIO)

    try:
        _main(argv)
    except Exception:  # pylint: disable=broad-except
        LOG = logging.getLogger(__name__)
        LOG.exception("Uncaught Exception")

    handleLogMessages(stringIO.getvalue())


# This method inspired by: https://stackoverflow.com/a/9534960/473672
def configureLogging(loglevel: int, stringIO: io.StringIO) -> None:
    rootLogger = logging.getLogger()
    rootLogger.setLevel(loglevel)

    handlers = []
    for handler in rootLogger.handlers:
        handlers.append(handler)
    for handler in handlers:
        rootLogger.removeHandler(handler)

    handler = logging.StreamHandler(stringIO)
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)-8s %(message)s", datefmt="%Y-%m-%d %H:%M:%S%Z"
    )
    handler.setFormatter(formatter)

    rootLogger.addHandler(handler)


def handleLogMessages(messages: Optional[str]) -> None:
    if not messages:
        return

    sys.stderr.write(ERROR_REPORTING_HEADER)
    sys.stderr.write("\n")

    # If this fails, run "tox.sh" once and the "version.py" file will be created
    # for you.
    #
    # NOTE: If we "import version" at the top of this file, we will depend on it
    # even if we don't use it. And this will make test avoidance fail to avoid
    # px.py tests every time you make a new commit (because committing recreates
    # version.py).
    from . import version  # pylint: disable=import-outside-toplevel

    sys.stderr.write("px version: " + version.VERSION + "\n")

    sys.stderr.write("\n")
    sys.stderr.write("Python version: " + sys.version + "\n")
    sys.stderr.write("\n")
    sys.stderr.write("Platform info: " + platform.platform() + "\n")
    sys.stderr.write("\n")
    sys.stderr.write(messages)
    sys.stderr.write("\n")
    sys.exit(1)


def _main(argv: List[str]) -> None:

    if "--install" in argv:
        install(argv)
        return

    if "--help" in argv:
        print(__doc__)
        return

    if "--version" in argv:
        # If this fails, run "tox.sh" once and the "version.py" file will be created for you.
        #
        # NOTE: If we "import version" at the top of this file, we will depend on it even if
        # we don't use it. And this will make test avoidance fail to avoid px.py tests every
        # time you make a new commit (because committing recreates version.py).
        from . import version  # pylint: disable=import-outside-toplevel

        print(version.VERSION)
        return

    with_pager: Optional[bool] = None
    with_color: Optional[bool] = None
    with_username = True
    top: bool = False
    sort_cpupercent: bool = False

    while "--no-pager" in argv:
        with_pager = False
        argv.remove("--no-pager")
    if with_pager is None:
        with_pager = sys.stdout.isatty()

    while "--color" in argv:
        with_color = True
        argv.remove("--color")
    if with_color is None:
        with_color = sys.stdout.isatty()
    if not with_color:
        px_terminal.disable_color()

    while "--top" in argv:
        top = True
        argv.remove("--top")
    if os.path.basename(argv[0]).endswith("top"):
        top = True

    while "--sort=cpupercent" in argv:
        sort_cpupercent = True
        argv.remove("--sort=cpupercent")

    while "--no-username" in argv:
        # Ref: https://github.com/walles/px/issues/88#issuecomment-945099485
        with_username = False
        argv.remove("--no-username")

    if len(argv) > 2:
        sys.stderr.write("ERROR: Expected zero or one argument but got more\n\n")
        print(__doc__)
        sys.exit(1)

    search = ""
    if len(argv) == 2:
        search = argv[1]

    if top:
        # Pulling px_top in on demand like this improves test result caching
        from . import px_top  # pylint: disable=import-outside-toplevel

        px_top.top(search=search)
        return

    try:
        pid = int(search)
        if not with_pager:
            px_processinfo.print_pid_info(sys.stdout.fileno(), pid)
            return

        # Page it!
        processes = px_process.get_all()
        process = px_processinfo.find_process_by_pid(pid, processes)
        if not process:
            sys.exit(f"No such PID: {pid}")

        px_pager.page_process_info(process, processes)
        return
    except ValueError:
        # It's a search filter and not a PID, keep moving
        pass

    procs = list(filter(lambda p: p.match(search), px_process.get_all()))

    columns: Optional[int] = None
    try:
        _, columns = px_terminal.get_window_size()
    except px_terminal.TerminalError:
        columns = None

    # Print the most interesting processes last; there are lots of processes and
    # the end of the list is where your eyes will be when you get the prompt back.
    procs = px_process.order_best_last(procs)
    if sort_cpupercent:
        procs = list(filter(lambda p: p.cpu_percent is not None, procs))
        procs = sorted(procs, key=operator.attrgetter("cpu_percent"))
    if search:
        # Put exact search matches last. Useful for "px cat" or other short
        # search strings with tons of hits.
        procs = sorted(procs, key=lambda p: p.command == search)
    lines = px_terminal.to_screen_lines(procs, None, None, with_username)

    if columns:
        for line in lines:
            print(px_terminal.crop_ansi_string_at_length(line, columns))
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
