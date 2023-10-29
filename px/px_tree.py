from . import px_process
from . import px_terminal

import sys

from typing import Set, List, Optional, Iterable


def tree(search: str) -> None:
    """Print a process tree"""
    print_me = _generate_tree(px_process.get_all(), search)
    if not print_me:
        print(f"No processes found matching <{search}>", file=sys.stderr)
        return

    for line in print_me:
        print(line)


def _generate_tree(processes: List[px_process.PxProcess], search: str) -> List[str]:
    if not processes:
        return []

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

            # Walk up the tree from this process, marking each process for display
            if process and process.parent:
                process = process.parent
            while process:
                if process.pid in show_pids:
                    break
                show_pids.add(process.pid)
                if not process.parent:
                    break
                process = process.parent

        # Search found nothing
        if not show_pids:
            return []

    lines = []
    coalescer = Coalescer(0)
    lines += coalescer.submit(processes[0], search)
    lines += coalescer.flush()
    return lines + _generate_child_tree(processes[0].children, 1, search, show_pids)


def _mark_children(process: px_process.PxProcess, show_pids: Set[int]) -> None:
    """Recursively mark all children of a search hit as needing to be shown"""
    show_pids.add(process.pid)
    for child in process.children:
        _mark_children(child, show_pids)


class Coalescer:
    def __init__(self, indent: int) -> None:
        self._base: Optional[px_process.PxProcess] = None
        self._count = 0
        self._indent = indent

    def submit(self, process: px_process.PxProcess, search: str) -> List[str]:
        """Returns an array of zero or more lines to be printed"""
        is_search_hit = search and process.match(search)
        has_children = bool(process.children)
        is_candidate = not is_search_hit and not has_children

        # If we can coalesce this, do it!
        if self._base and is_candidate and self._base.command == process.command:
            self._count += 1
            return []
        if not self._base and is_candidate:
            self._base = process
            self._count = 1
            return []

        return_me = []

        # Otherwise, print the coalesced line if we have one
        if self._base:
            return_me += self.flush()

        # Can we coalesce this line?
        if is_candidate:
            self._base = process
            self._count = 1
            return return_me

        # And print the current line
        if is_search_hit:
            return_me.append(
                f"{'  ' * self._indent}{px_terminal.bold(process.command)}({process.pid})"
            )
        else:
            return_me.append(f"{'  ' * self._indent}{process.command}({process.pid})")

        return return_me

    def flush(self) -> List[str]:
        if not self._base:
            return []

        assert self._count > 0

        return_me: str
        if self._count == 1:
            return_me = f"{'  ' * self._indent}{self._base.command}({self._base.pid})"
        else:
            return_me = f"{'  ' * self._indent}{self._base.command}... ({px_terminal.bold(f'{self._count}×')})"

        self._base = None
        self._count = 0

        return [return_me]


def _generate_child_tree(
    children: Iterable[px_process.PxProcess],
    indent: int,
    search: str,
    show_pids: Set[int],
) -> List[str]:
    lines = []

    coalescer = Coalescer(indent)
    for child in sorted(
        children, key=lambda p: (p.command.lower(), bool(p.children), p.pid)
    ):
        if show_pids and child.pid not in show_pids:
            continue

        lines += coalescer.submit(child, search)
        lines += _generate_child_tree(child.children, indent + 1, search, show_pids)

    lines += coalescer.flush()
    return lines
