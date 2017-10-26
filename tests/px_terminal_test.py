# coding=utf-8

import sys

from px import px_terminal

import testutils


def test_to_screen_lines_unbounded():
    procs = [testutils.create_process(commandline="/usr/bin/fluff 1234")]
    assert px_terminal.to_screen_lines(procs, None) == [
        "  PID COMMAND USERNAME   CPU RAM COMMANDLINE",
        "47536 fluff   root     0.03s  0% /usr/bin/fluff 1234"
    ]


def test_to_screen_lines_unicode():
    procs = [testutils.create_process(commandline=u"/usr/bin/😀")]
    converted = px_terminal.to_screen_lines(procs, None)
    if sys.version_info.major > 3:
        assert converted == [
            "  PID COMMAND USERNAME   CPU RAM COMMANDLINE",
            "47536 😀       root     0.03s  0% /usr/bin/😀"
        ]
    else:
        # Unicode string widths are difficult before Python 3.3, don't test
        # the actual layout in this case:
        # https://stackoverflow.com/q/29109944/473672
        pass


def test_get_string_of_length():
    assert px_terminal.get_string_of_length("12345", 3) == "123"
    assert px_terminal.get_string_of_length("12345", 5) == "12345"
    assert px_terminal.get_string_of_length("12345", 7) == "12345  "
    assert px_terminal.get_string_of_length("12345", None) == "12345"
