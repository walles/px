from . import px_process
from . import px_terminal

from typing import Set


def tree(search: str) -> None:
    """Print a process tree"""

    # Only print subtrees needed for showing all search hits and their children.
    #
    # We do that by starting at the search hits and walking up the tree from all
    # of them, collecting each PID we see along the way. Then when we render the
    # tree, we only render those PIDs.
    show_pids: Set[int] = set()
    if search:
        for process in px_process.get_all():
            if not process.match(search):
                continue

            _mark_children(process, show_pids)

            while process:
                if process.pid in show_pids:
                    break
                show_pids.add(process.pid)
                if not process.parent:
                    break
                process = process.parent

    procs = px_process.get_all()
    if not procs:
        return

    _print_subtree(procs[0], 0, search, show_pids)


# Recursively mark all children of the search hit as needing to be
# shown
def _mark_children(process: px_process.PxProcess, show_pids: Set[int]) -> None:
    show_pids.add(process.pid)
    for child in process.children:
        _mark_children(child, show_pids)


def _print_subtree(
    process: px_process.PxProcess, indent: int, search: str, show_pids: Set[int]
) -> None:
    if show_pids and process.pid not in show_pids:
        return

    print("  " * indent, end="")

    if search and process.match(search):
        print(f"{px_terminal.bold(process.command)}({process.pid})")
    else:
        print(f"{process.command}({process.pid})")

    # FIXME: Unless they are search hits, coalesce leaf nodes that have the same
    # names
    for child in sorted(process.children, key=lambda p: (p.command.lower(), p.pid)):
        if show_pids and child.pid not in show_pids:
            continue

        _print_subtree(child, indent + 1, search, show_pids)
