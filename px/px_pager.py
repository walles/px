import sys
import subprocess

from . import px_processinfo

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process  # NOQA
    from typing import List   # NOQA


def page_process_info(process, processes):
    # type: (px_process.PxProcess, List[px_process.PxProcess]) -> None

    # FIXME: Get a suitable pager + command line options based on the $PAGER variable
    pager = subprocess.Popen(['moar'], stdin=subprocess.PIPE)
    pager_stdin = pager.stdin
    assert pager_stdin is not None

    # FIXME: If the pager goes away before we're done with this, arrow buttons
    # don't work any more after coming back into ptop
    px_processinfo.print_process_info(pager_stdin.fileno(), process, processes)

    pager_stdin.close()

    # FIXME: If this returns an error code, what do we do?
    pager.wait()
