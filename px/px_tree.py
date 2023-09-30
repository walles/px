from . import px_process


def tree(search: str) -> None:
    """Print a process tree"""

    # FIXME: Do something useful with search

    procs = px_process.get_all()
    if not procs:
        return

    _print_subtree(procs[0], 0)

    # FIXME: Verify we got to all processes


def _print_subtree(process: px_process.PxProcess, indent: int) -> None:
    print("  " * indent, end="")

    # FIXME: Highlight search hits
    print(f"{process.command}({process.pid})")

    # FIXME: Unless they are search hits, coalesce leaf nodes that have the same
    # names
    for child in sorted(process.children, key=lambda p: p.command.lower()):
        _print_subtree(child, indent + 1)
