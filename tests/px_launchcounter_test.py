from px import px_terminal
from px import px_launchcounter

from . import testutils


def test_list_new_launches():
    process = testutils.create_process(pid=100, timestring="Mon Apr  7 09:33:11 2010")
    process_identical = testutils.create_process(
        pid=100, timestring="Mon Apr  7 09:33:11 2010"
    )
    process_other_pid = testutils.create_process(
        pid=101, timestring="Mon Apr  7 09:33:11 2010"
    )
    process_other_starttime = testutils.create_process(
        pid=100, timestring="Mon Apr  8 09:33:11 2010"
    )

    before = [process]
    after = [process_identical, process_other_pid, process_other_starttime]

    new_processes = px_launchcounter._list_new_launches(before, after)

    # We should get unicode responses from getch()
    assert new_processes == [process_other_pid, process_other_starttime]


def test_get_screen_lines_coalesces():
    px_terminal._enable_color = True
    # If we have both "init"->"iTerm" and "init"->"iTerm"->"fish",
    # they should be reported as just "init"->"iTerm"->"fish".
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches(
        [
            testutils.fake_callchain("init", "iTerm"),
            testutils.fake_callchain("init", "iTerm", "fish"),
        ]
    )
    lines = launchcounter.get_screen_lines()
    assert lines == [
        "init -> "
        + px_terminal.bold("iTerm")
        + "(1) -> "
        + px_terminal.bold("fish")
        + "(1)"
    ]

    # Then the same thing backwards
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches(
        [
            testutils.fake_callchain("init", "iTerm", "fish"),
            testutils.fake_callchain("init", "iTerm"),
        ]
    )
    lines = launchcounter.get_screen_lines()
    assert lines == [
        "init -> "
        + px_terminal.bold("iTerm")
        + "(1) -> "
        + px_terminal.bold("fish")
        + "(1)"
    ]


def test_print_launch_counts():
    px_terminal._enable_color = True
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches(
        [
            testutils.fake_callchain("init", "iTerm"),
            testutils.fake_callchain("init", "iTerm", "fish"),
            testutils.fake_callchain("init", "iTerm", "fish"),
            testutils.fake_callchain("init", "iTerm"),
            testutils.fake_callchain("init", "iTerm"),
        ]
    )
    lines = launchcounter.get_screen_lines()
    assert lines == [
        "init -> "
        + px_terminal.bold("iTerm")
        + "(3) -> "
        + px_terminal.bold("fish")
        + "(2)"
    ]


def test_ignore_surrounding_parentheses():
    px_terminal._enable_color = True
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches(
        [
            testutils.fake_callchain("init", "iTerm"),
            testutils.fake_callchain("init", "iTerm"),
            testutils.fake_callchain("init", "(iTerm)"),
            testutils.fake_callchain("init", "iTerm()"),
            testutils.fake_callchain("init", "i(Term)"),
            testutils.fake_callchain("init", "(i)Term"),
        ]
    )
    lines = launchcounter.get_screen_lines()

    # Note that the ordering of the lines doesn't really matter here, just as
    # long as all of them are in there
    assert set(lines) == {
        "init -> " + px_terminal.bold("iTerm") + "(3)",
        "init -> " + px_terminal.bold("(i)Term") + "(1)",
        "init -> " + px_terminal.bold("i(Term)") + "(1)",
        "init -> " + px_terminal.bold("iTerm()") + "(1)",
    }


def test_to_tuple_list():
    assert px_launchcounter._to_tuple_list(("a", "b", "c"), 5) == [
        ("a", 0),
        ("b", 0),
        ("c", 5),
    ]

    assert px_launchcounter._to_tuple_list(("a",), 5) == [("a", 5)]


def test_merge_tuple_lists():
    l1 = [("a", 0), ("b", 2), ("c", 5)]
    l2 = [("a", 0), ("b", 4)]
    l3 = [("a", 0), ("e", 4)]

    assert px_launchcounter._merge_tuple_lists(l1, l2) == [("a", 0), ("b", 6), ("c", 5)]

    assert px_launchcounter._merge_tuple_lists(l1, l3) is None


def test_sort_launchers_lists():
    l1 = [("a", 3), ("b", 4)]
    l2 = [("a", 5), ("e", 0)]

    # List with highest individual number should come first
    assert px_launchcounter.sort_launchers_list([l1, l2]) == [l2, l1]
    assert px_launchcounter.sort_launchers_list([l2, l1]) == [l2, l1]
