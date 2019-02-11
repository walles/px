import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process   # NOQA
    from six import text_type  # NOQA
    from typing import List    # NOQA
    from typing import Tuple   # NOQA
    from typing import Dict    # NOQA
    from typing import Optional  # NOQA


class Launchcounter(object):
    def __init__(self):
        self._hierarchies = {}  # type: Dict[Tuple[text_type, ...], int]

        # Most recent process snapshot
        self._last_processlist = None  # type: Optional[List[px_process.PxProcess]]

    def _callchain(self, process):
        # type: (px_process.PxProcess) -> Tuple[text_type, ...]

        reverse_callchain = []  # type: List[text_type]

        current = process  # type: Optional[px_process.PxProcess]
        while current is not None:
            reverse_callchain.append(current.command)
            current = current.parent

        return tuple(reversed(reverse_callchain))

    def _register_launches(self, new_processes):
        # type: (List[px_process.PxProcess]) -> None

        for new_process in new_processes:
            callchain = self._callchain(new_process)
            if callchain in self._hierarchies:
                self._hierarchies[callchain] += 1
            else:
                self._hierarchies[callchain] = 1

    def _list_new_launches(
        self,
        before,  # type: List[px_process.PxProcess]
        after    # type: List[px_process.PxProcess]
    ):
        # type: (...) -> List[px_process.PxProcess]
        pid2oldProc = {}  # type: Dict[int,px_process.PxProcess]
        for old_proc in before:
            pid2oldProc[old_proc.pid] = old_proc

        new_procs = []  # List[px_process.PxProcess]
        for new_proc in after:
            if new_proc.pid not in pid2oldProc:
                # This is a new process
                new_procs.append(new_proc)
                continue

            old_proc = pid2oldProc[new_proc.pid]
            if old_proc.start_time != new_proc.start_time:
                # This is a new process, PID has been reused
                new_procs.append(new_proc)
                continue

        return new_procs

    def update(self, procs_snapshot):
        # type: (List[px_process.PxProcess]) -> None

        if self._last_processlist is None:
            self._last_processlist = procs_snapshot
            return

        new_processes = self._list_new_launches(self._last_processlist, procs_snapshot)
        self._register_launches(new_processes)

        self._last_processlist = procs_snapshot

    def get_screen_lines(self, rows, columns):
        # type: (int, int) -> List[text_type]

        # FIXME: Render this as a tree, not a list
        # FIXME: Should we sort the tree somehow?
        # FIXME: Should we print counts somewhere?
        # FIXME: How to handle rows?
        lines = []  # type: List[text_type]
        for row in sorted(self._hierarchies.keys()):
            count = self._hierarchies[row]
            lines.append('{}: {}'.format(str(row), count))

        return lines
