import sys

from . import px_terminal

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process   # NOQA
    from six import text_type  # NOQA
    from typing import List    # NOQA
    from typing import Tuple   # NOQA
    from typing import Dict    # NOQA
    from typing import Optional  # NOQA


def render_launch_tuple(launch_tuple):
    # type: (Tuple[text_type, int]) -> text_type
    binary = launch_tuple[0]
    count = launch_tuple[1]
    if count == 0:
        return binary
    else:
        return px_terminal.bold(binary) + "(" + str(count) + ")"


def _get_minus_max_score(tuples_list):
    # type: (List[Tuple[text_type, int]]) -> int
    max_score = 0
    for tuple in tuples_list:
        max_score = max(max_score, tuple[1])
    return -max_score


def sort_launchers_list(launchers_list):
    # type: (List[List[Tuple[text_type, int]]]) -> List[List[Tuple[text_type, int]]]
    return sorted(launchers_list, key=_get_minus_max_score)


class Launchcounter(object):
    def __init__(self):
        self._hierarchies = {}  # type: Dict[Tuple[text_type, ...], int]

        # Most recent process snapshot
        self._last_processlist = None  # type: Optional[List[px_process.PxProcess]]

    def _strip_parentheses(self, s):
        # type: (text_type) -> text_type
        if not s:
            return s
        if s[0] != '(':
            return s
        if s[-1] != ')':
            return s
        return s[1:-1]

    def _callchain(self, process):
        # type: (px_process.PxProcess) -> Tuple[text_type, ...]

        reverse_callchain = []  # type: List[text_type]

        current = process  # type: Optional[px_process.PxProcess]
        while current is not None:
            reverse_callchain.append(self._strip_parentheses(current.command))
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

    def _to_tuple_list(self, launcher_list, count):
        # type: (Tuple[text_type, ...], int) -> List[Tuple[text_type, int]]
        """
        Converts from: (("a", "b", "c"), 5)
                 to  : [("a", 0), ("b", 0), ("c", 5)]
        """
        tuple_list = []  # type: List[Tuple[text_type, int]]
        for launcher in launcher_list:
            tuple_list.append((launcher, 0))
        tuple_list[-1] = (launcher_list[-1], count)
        return tuple_list

    def _merge_tuple_lists(
        self,
        tl1,  # type: List[Tuple[text_type, int]]
        tl2   # type: List[Tuple[text_type, int]]
    ):
        # type: (...) -> Optional[List[Tuple[text_type, int]]]
        if len(tl1) > len(tl2):
            longer = tl1
            shorter = tl2
        else:
            longer = tl2
            shorter = tl1

        merged = longer[:]
        for i in range(0, len(shorter)):
            t1 = shorter[i]
            t2 = longer[i]
            if t1[0] != t2[0]:
                # Mismatch, we can't merge these
                return None
            merged[i] = (t1[0], t1[1] + t2[1])

        return merged

    def _coalesce_launchers(self):
        # type: () -> List[List[Tuple[text_type, int]]]
        coalesced = []  # type: List[List[Tuple[text_type, int]]]

        for launcher_list in sorted(self._hierarchies.keys()):
            count = self._hierarchies[launcher_list]

            new_tuple_list = self._to_tuple_list(launcher_list, count)
            if len(coalesced) == 0:
                coalesced.append(new_tuple_list)
                continue

            merged = self._merge_tuple_lists(coalesced[-1], new_tuple_list)
            if merged:
                coalesced[-1] = merged
            else:
                coalesced.append(new_tuple_list)

        return coalesced

    def get_screen_lines(self, columns):
        # type: (int) -> List[text_type]

        launchers_list = self._coalesce_launchers()
        launchers_list = sort_launchers_list(launchers_list)

        lines = []  # type: List[text_type]
        for row in launchers_list:
            line = u' -> '.join(map(render_launch_tuple, row))
            lines.append(px_terminal.crop_ansi_string_at_length(line, columns))

        return lines
