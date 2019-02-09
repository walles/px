import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process   # NOQA
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

    def update(self, procs_snapshot):
        # type: (List[px_process.PxProcess]) -> None
        pass

    def get_launched_screen_lines(self, rows, columns):
        # type: (int, int) -> List[text_type]
        return ["FIXME"] * rows

    def get_launchers_screen_lines(self, rows, columns):
        # type: (int, int) -> List[text_type]
        return ["FIXME"] * rows
