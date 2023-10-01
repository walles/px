from px import px_tree
from px import px_terminal
from px import px_process

from . import testutils

from typing import List
import datetime
import dateutil.tz


def resolve(processes: List[px_process.PxProcess]) -> List[px_process.PxProcess]:
    now = datetime.datetime.now().replace(tzinfo=dateutil.tz.tzlocal())

    process_dict = {p.pid: p for p in processes}
    px_process.resolve_links(process_dict, now)

    return processes


def test_empty():
    assert px_tree._generate_tree([], "") == []


def test_parent_child():
    assert px_tree._generate_tree(
        resolve(
            [
                testutils.create_process(pid=1, ppid=0, commandline="parent"),
                testutils.create_process(pid=2, ppid=1, commandline="child"),
            ]
        ),
        "",
    ) == ["parent(1)", "  child(2)"]


def test_search():
    assert px_tree._generate_tree(
        resolve(
            [
                testutils.create_process(pid=1, ppid=0, commandline="root"),
                testutils.create_process(pid=2, ppid=1, commandline="find-me"),
                testutils.create_process(pid=3, ppid=1, commandline="uninteresting"),
            ]
        ),
        "find-me",
    ) == ["root(1)", f"  {px_terminal.bold('find-me')}(2)"]
