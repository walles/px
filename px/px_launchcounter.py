from . import px_terminal

from . import px_process
from typing import List
from typing import Tuple
from typing import Dict
from typing import Optional


def render_launch_tuple(launch_tuple: Tuple[str, int]) -> str:
    binary = launch_tuple[0]
    count = launch_tuple[1]
    if count == 0:
        return binary

    return px_terminal.bold(binary) + "(" + str(count) + ")"


def _get_minus_max_score(tuples_list: List[Tuple[str, int]]) -> int:
    max_score = 0
    for current_tuple in tuples_list:
        max_score = max(max_score, current_tuple[1])
    return -max_score


def sort_launchers_list(
    launchers_list: List[List[Tuple[str, int]]]
) -> List[List[Tuple[str, int]]]:
    return sorted(launchers_list, key=_get_minus_max_score)


def _strip_parentheses(s: str) -> str:
    if not s:
        return s
    if s[0] != "(":
        return s
    if s[-1] != ")":
        return s
    return s[1:-1]


def _list_new_launches(
    before: List[px_process.PxProcess],
    after: List[px_process.PxProcess],
) -> List[px_process.PxProcess]:
    pid2oldProc: Dict[int, px_process.PxProcess] = {}
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


def _to_tuple_list(launcher_list: Tuple[str, ...], count: int) -> List[Tuple[str, int]]:
    """
    Converts from: (("a", "b", "c"), 5)
                to  : [("a", 0), ("b", 0), ("c", 5)]
    """
    tuple_list: List[Tuple[str, int]] = []
    for launcher in launcher_list:
        tuple_list.append((launcher, 0))
    tuple_list[-1] = (launcher_list[-1], count)
    return tuple_list


def _merge_tuple_lists(
    tl1: List[Tuple[str, int]],
    tl2: List[Tuple[str, int]],
) -> Optional[List[Tuple[str, int]]]:
    if len(tl1) > len(tl2):
        longer = tl1
        shorter = tl2
    else:
        longer = tl2
        shorter = tl1

    merged = longer[:]
    for i, t1 in enumerate(shorter):
        t2 = longer[i]
        if t1[0] != t2[0]:
            # Mismatch, we can't merge these
            return None
        merged[i] = (t1[0], t1[1] + t2[1])

    return merged


def _callchain(process: px_process.PxProcess) -> Tuple[str, ...]:

    reverse_callchain: List[str] = []

    current: Optional[px_process.PxProcess] = process
    while current is not None:
        reverse_callchain.append(_strip_parentheses(current.command))
        current = current.parent

    return tuple(reversed(reverse_callchain))


class Launchcounter:
    def __init__(self):
        self._hierarchies: Dict[Tuple[str, ...], int] = {}

        # Most recent process snapshot
        self._last_processlist: Optional[List[px_process.PxProcess]] = None

    def _register_launches(self, new_processes: List[px_process.PxProcess]) -> None:
        for new_process in new_processes:
            callchain = _callchain(new_process)
            if callchain in self._hierarchies:
                self._hierarchies[callchain] += 1
            else:
                self._hierarchies[callchain] = 1

    def update(self, procs_snapshot: List[px_process.PxProcess]) -> None:

        if self._last_processlist is None:
            self._last_processlist = procs_snapshot
            return

        new_processes = _list_new_launches(self._last_processlist, procs_snapshot)
        self._register_launches(new_processes)

        self._last_processlist = procs_snapshot

    def _coalesce_launchers(self) -> List[List[Tuple[str, int]]]:
        coalesced: List[List[Tuple[str, int]]] = []

        for launcher_list in sorted(self._hierarchies.keys()):
            count = self._hierarchies[launcher_list]

            new_tuple_list = _to_tuple_list(launcher_list, count)
            if len(coalesced) == 0:
                coalesced.append(new_tuple_list)
                continue

            merged = _merge_tuple_lists(coalesced[-1], new_tuple_list)
            if merged:
                coalesced[-1] = merged
            else:
                coalesced.append(new_tuple_list)

        return coalesced

    def get_screen_lines(self) -> List[str]:

        launchers_list = self._coalesce_launchers()
        launchers_list = sort_launchers_list(launchers_list)

        lines: List[str] = []
        for row in launchers_list:
            line = " -> ".join(map(render_launch_tuple, row))
            lines.append(line)

        return lines
