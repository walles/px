from . import px_process
from . import px_terminal

from typing import Set, List


def tree(search: str) -> None:
    """Print a process tree"""
    for line in _generate_tree(px_process.get_all(), search):
        print(line)


def _generate_tree(processes: List[px_process.PxProcess], search: str) -> List[str]:
    # Only print subtrees needed for showing all search hits and their children.
    #
    # We do that by starting at the search hits and walking up the tree from all
    # of them, collecting each PID we see along the way. Then when we render the
    # tree, we only render those PIDs.
    show_pids: Set[int] = set()
    if search:
        for process in processes:
            if not process.match(search):
                continue

            _mark_children(process, show_pids)

            if process and process.parent:
                process = process.parent
            while process:
                if process.pid in show_pids:
                    break
                show_pids.add(process.pid)
                if not process.parent:
                    break
                process = process.parent

    if not processes:
        return []

    return _generate_subtree(processes[0], 0, search, show_pids)


def _mark_children(process: px_process.PxProcess, show_pids: Set[int]) -> None:
    """Recursively mark all children of a search hit as needing to be shown"""
    show_pids.add(process.pid)
    for child in process.children:
        _mark_children(child, show_pids)


def _generate_subtree(
    process: px_process.PxProcess, indent: int, search: str, show_pids: Set[int]
) -> List[str]:
    if show_pids and process.pid not in show_pids:
        return []

    line: str
    if search and process.match(search):
        line = f"{px_terminal.bold(process.command)}({process.pid})"
    else:
        line = f"{process.command}({process.pid})"
    lines = ["  " * indent + line]

    # FIXME: Unless they are search hits, coalesce leaf nodes that have the same
    # names
    for child in sorted(process.children, key=lambda p: (p.command.lower(), p.pid)):
        if show_pids and child.pid not in show_pids:
            continue

        lines += _generate_subtree(child, indent + 1, search, show_pids)

    return lines
