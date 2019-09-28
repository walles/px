import os
import sys
import threading
import subprocess

from . import px_processinfo

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process  # NOQA
    from typing import List   # NOQA


def _pump_info_to_fd(fileno, process, processes):
    # type: (int, px_process.PxProcess, List[px_process.PxProcess]) -> None
    try:
        px_processinfo.print_process_info(fileno, process, processes)
        os.close(fileno)
    except Exception:
        # Ignore exceptions; we can get those if the pager hangs / goes away
        # unexpectedly, and we really don't care about those.

        # FIXME: Should we report this to the user? How and where in that case?
        pass


def launch_pager():
    # FIXME: Get a suitable pager + command line options based on the $PAGER
    # variable
    return subprocess.Popen(['moar'], stdin=subprocess.PIPE)


def page_process_info(process, processes):
    # type: (px_process.PxProcess, List[px_process.PxProcess]) -> None

    pager = launch_pager()
    pager_stdin = pager.stdin
    assert pager_stdin is not None

    # Do this in a thread to avoid problems if the pager hangs / goes away
    # unexpectedly
    info_thread = threading.Thread(
        target=_pump_info_to_fd,
        args=(pager_stdin.fileno(), process, processes))
    info_thread.setDaemon(True)  # Exiting while this is running is fine
    info_thread.start()

    # FIXME: If this returns an error code, what do we do?
    pager.wait()
