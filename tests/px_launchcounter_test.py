from px import px_launchcounter

from . import testutils


def test_list_new_launches():
    process = \
        testutils.create_process(pid=100, timestring="Mon Apr 7 09:33:11 2010")
    process_identical = \
        testutils.create_process(pid=100, timestring="Mon Apr 7 09:33:11 2010")
    process_other_pid = \
        testutils.create_process(pid=101, timestring="Mon Apr 7 09:33:11 2010")
    process_other_starttime = \
        testutils.create_process(pid=100, timestring="Mon Apr 8 09:33:11 2010")

    before = [process]
    after = [process_identical, process_other_pid, process_other_starttime]

    new_processes = px_launchcounter.Launchcounter()._list_new_launches(before, after)

    # We should get unicode responses from getch()
    assert new_processes == [process_other_pid, process_other_starttime]


def test_get_screen_lines_coalesces():
    # If we have both "init"->"iTerm" and "init"->"iTerm"->"fish",
    # they should be reported as just "init"->"iTerm"->"fish".
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches([
        testutils.fake_callchain('init', 'iTerm'),
        testutils.fake_callchain('init', 'iTerm', 'fish'),
    ])
    lines = launchcounter.get_screen_lines(100)
    assert lines == ['init -> iTerm (1) -> fish (1)']

    # Then the same thing backwards
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches([
        testutils.fake_callchain('init', 'iTerm', 'fish'),
        testutils.fake_callchain('init', 'iTerm'),
    ])
    lines = launchcounter.get_screen_lines(100)
    assert lines == ['init -> iTerm (1) -> fish (1)']


def test_print_launch_counts():
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches([
        testutils.fake_callchain('init', 'iTerm'),
        testutils.fake_callchain('init', 'iTerm', 'fish'),
        testutils.fake_callchain('init', 'iTerm', 'fish'),
        testutils.fake_callchain('init', 'iTerm'),
        testutils.fake_callchain('init', 'iTerm'),
    ])
    lines = launchcounter.get_screen_lines(100)
    assert lines == ['init -> iTerm (3) -> fish (2)']


def test_to_tuple_list():
    launchcounter = px_launchcounter.Launchcounter()
    assert \
        launchcounter._to_tuple_list(("a", "b", "c"), 5) == \
        [("a", 0), ("b", 0), ("c", 5)]

    assert launchcounter._to_tuple_list(("a",), 5) == [("a", 5)]


def test_merge_tuple_lists():
    launchcounter = px_launchcounter.Launchcounter()
    l1 = [(u"a", 0), (u"b", 2), (u"c", 5)]
    l2 = [(u"a", 0), (u"b", 4)]
    l3 = [(u"a", 0), (u"e", 4)]

    assert launchcounter._merge_tuple_lists(l1, l2) == \
        [(u"a", 0), (u"b", 6), (u"c", 5)]

    assert launchcounter._merge_tuple_lists(l1, l3) is None


def test_sort_launchers_lists():
    l1 = [(u"a", 3), (u"b", 4)]
    l2 = [(u"a", 5), (u"e", 0)]

    # List with highest individual number should come first
    assert px_launchcounter.sort_launchers_list([l1, l2]) == [l2, l1]
    assert px_launchcounter.sort_launchers_list([l2, l1]) == [l2, l1]


def test_get_screen_lines_column_cutoff():
    # If we have both "init"->"iTerm" and "init"->"iTerm"->"fish",
    # they should be reported as just "init"->"iTerm"->"fish".
    launchcounter = px_launchcounter.Launchcounter()
    launchcounter._register_launches([
        testutils.fake_callchain('init', 'iTerm'),
        testutils.fake_callchain('init', 'iTerm', 'fish'),
    ])
    lines = launchcounter.get_screen_lines(10)
    assert lines == ['init -> iT']
