import sys

from . import px_process   # NOQA

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List    # NOQA
    from typing import Dict    # NOQA
    from typing import Tuple   # NOQA
    from typing import Optional  # NOQA
    from six import text_type  # NOQA


class Launchcounter(object):
    def __init__(self):
        self._binaries = {}  # type: Dict[text_type,int]

        # This is a mapping of processes into direct and indirect
        # launch counts. The direct one is updated if this process
        # launches a process by itself. The indirect one is updated
        # when a (grand)child of this process launches something.
        self._launchers = {}  # type: Dict[px_process.PxProcess, Tuple[int, int]]

        # Most recent process snapshot
        self._last_processlist = None  # type: Optional[List[px_process.PxProcess]]

    def _register_launch(self, new_process):
        # type: (px_process.PxProcess) -> None

        # FIXME: Collect stats here

        pass

    def update(self, procs_snapshot):
        # type: (List[px_process.PxProcess]) -> None

        if self._last_processlist is None:
            self._last_processlist = procs_snapshot
            return

        # Look for newly launched binaries
        pid2oldProc = {}  # type: Dict[int,px_process.PxProcess]
        for old_proc in self._last_processlist:
            pid2oldProc[old_proc.pid] = old_proc

        for new_proc in procs_snapshot:
            if old_proc.pid not in pid2oldProc:
                # This is a new process
                self._register_launch(new_proc)
                continue

            old_proc = pid2oldProc[new_proc.pid]
            if old_proc.start_time != new_proc.start_time:
                # This is a new process, PID has been reused
                self._register_launch(new_proc)
                continue

        self._last_processlist = procs_snapshot

    def get_launched_screen_lines(self, rows, columns):
        # type: (int, int) -> List[text_type]
        return ["FIXME"] * rows

    def get_launchers_screen_lines(self, rows, columns):
        # type: (int, int) -> List[text_type]
        return ["FIXME"] * rows
