from px import px_tree
from px import px_terminal
from px import px_process

from . import testutils

from typing import List
import datetime


def resolve(processes: List[px_process.PxProcess]) -> List[px_process.PxProcess]:
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()

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


def test_no_search():
    assert px_tree._generate_tree(
        resolve(
            [
                testutils.create_process(pid=1, ppid=0, commandline="root"),
                testutils.create_process(pid=2, ppid=1, commandline="find-me"),
                testutils.create_process(pid=3, ppid=1, commandline="uninteresting"),
            ]
        ),
        "",
    ) == ["root(1)", "  find-me(2)", "  uninteresting(3)"]


def test_search_no_matches():
    assert (
        px_tree._generate_tree(
            resolve(
                [
                    testutils.create_process(pid=1, ppid=0, commandline="root"),
                    testutils.create_process(pid=2, ppid=1, commandline="find-me"),
                    testutils.create_process(
                        pid=3, ppid=1, commandline="uninteresting"
                    ),
                ]
            ),
            "not-there",
        )
        == []
    )


def test_coalesce_no_search():
    assert px_tree._generate_tree(
        resolve(
            [
                testutils.create_process(pid=1, ppid=0, commandline="root"),
                testutils.create_process(pid=2, ppid=1, commandline="process"),
                testutils.create_process(pid=3, ppid=1, commandline="process"),
            ]
        ),
        "",
    ) == ["root(1)", f"  process... ({px_terminal.bold('2×')})"]


def test_coalesce_with_search():
    assert px_tree._generate_tree(
        resolve(
            [
                testutils.create_process(pid=1, ppid=0, commandline="root"),
                testutils.create_process(pid=2, ppid=1, commandline="process"),
                testutils.create_process(pid=3, ppid=1, commandline="process"),
            ]
        ),
        "process",
    ) == [
        "root(1)",
        f"  {px_terminal.bold('process')}(2)",
        f"  {px_terminal.bold('process')}(3)",
    ]


def test_coalesce_no_leaf():
    assert px_tree._generate_tree(
        resolve(
            [
                testutils.create_process(pid=1, ppid=0, commandline="root"),
                testutils.create_process(pid=2, ppid=1, commandline="process"),
                testutils.create_process(pid=3, ppid=1, commandline="process"),
                testutils.create_process(pid=4, ppid=1, commandline="process"),
                testutils.create_process(pid=5, ppid=1, commandline="process"),
                testutils.create_process(pid=6, ppid=1, commandline="process"),
                testutils.create_process(pid=7, ppid=4, commandline="subprocess"),
            ]
        ),
        "",
    ) == [
        "root(1)",
        f"  process... ({px_terminal.bold('4×')})",
        "  process(4)",
        "    subprocess(7)",
    ]


def test_coalescer():
    test_me = px_tree.Coalescer(0)
    assert not test_me.submit(testutils.create_process(pid=1, commandline="Kuala"), "")
    assert test_me.submit(testutils.create_process(commandline="Lumpur"), "") == [
        "Kuala(1)"
    ]
    assert not test_me.submit(testutils.create_process(commandline="Lumpur"), "")
    assert not test_me.submit(testutils.create_process(commandline="Lumpur"), "")
    assert test_me.flush() == [f"Lumpur... ({px_terminal.bold('3×')})"]
