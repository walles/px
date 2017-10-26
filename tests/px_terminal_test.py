# coding=utf-8

from px import px_terminal

import testutils


def test_to_screen_lines_unbounded():
    procs = [testutils.create_process(commandline="/usr/bin/fluff 1234")]
    assert px_terminal.to_screen_lines(procs, None) == [
        "  PID COMMAND USERNAME   CPU RAM COMMANDLINE",
        "47536 fluff   root     0.03s  0% /usr/bin/fluff 1234"
    ]


def test_to_screen_lines_unicode():
    procs = [testutils.create_process(commandline="/usr/bin/😀")]
    assert px_terminal.to_screen_lines(procs, None) == [
        "  PID COMMAND USERNAME   CPU RAM COMMANDLINE",
        "47536 😀       root     0.03s  0% /usr/bin/😀"
    ]


def test_get_string_of_length():
    assert px_terminal.get_string_of_length("12345", 3) == "123"
    assert px_terminal.get_string_of_length("12345", 5) == "12345"
    assert px_terminal.get_string_of_length("12345", 7) == "12345  "
    assert px_terminal.get_string_of_length("12345", None) == "12345"
