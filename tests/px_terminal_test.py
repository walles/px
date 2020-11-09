# coding=utf-8

import os
import sys

from px import px_terminal

from . import testutils

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List    # NOQA
    from six import text_type  # NOQA


def test_to_screen_lines_unbounded():
    procs = [testutils.create_process(commandline="/usr/bin/fluff 1234")]
    assert px_terminal.to_screen_lines(procs, None, None, None) == [
        "\x1b[1m  PID COMMAND USERNAME CPU CPUTIME RAM COMMANDLINE\x1b[22m",
        "47536 fluff   root     "
        + px_terminal.faint(" 0%")
        + " "
        + px_terminal.bold("  0.03s")
        + " "
        + px_terminal.faint(" 0%")
        + " /usr/bin/fluff 1234"
    ]


def test_to_screen_lines_bounded():
    procs = [testutils.create_process(commandline="/usr/bin/fluff 1234")]
    assert px_terminal.to_screen_lines(procs, 50, None, None) == [
        "\x1b[1m  PID COMMAND USERNAME CPU CPUTIME RAM COMMANDLINE\x1b[22m",
        "47536 fluff   root     "
        + px_terminal.faint(" 0%")
        + " "
        + px_terminal.bold("  0.03s")
        + " "
        + px_terminal.faint(" 0%")
        + " /usr/bin/fl\x1b[0m"
    ]


def test_crop_heading_lines():
    procs = [testutils.create_process(commandline="/usr/bin/fluff 1234")]
    assert px_terminal.to_screen_lines(procs, 10, None, None) == [
        "\x1b[1m  PID COMM\x1b[22m",
        "47536 fluf"
    ]


def test_to_screen_lines_unicode():
    procs = [testutils.create_process(commandline=u"/usr/bin/😀")]
    converted = px_terminal.to_screen_lines(procs, None, None, None)
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
    CSI = u"\x1b["

    assert px_terminal.get_string_of_length("12345", 3) == "123"
    assert px_terminal.get_string_of_length("12345", 5) == "12345"
    assert px_terminal.get_string_of_length("12345", 7) == "12345  "
    assert px_terminal.get_string_of_length("12345", None) == "12345"

    # Test with escaped strings
    mid_bold = "1" + px_terminal.bold("234") + "5"
    assert px_terminal.get_string_of_length(mid_bold, 6) == mid_bold + " "
    assert px_terminal.get_string_of_length(mid_bold, 3) == \
        "1" + CSI + "1m23" + CSI + "0m"


def test_crop_ansi_string_at_length():
    CSI = u"\x1b["

    # Non-formatted cropping
    assert px_terminal.crop_ansi_string_at_length("", 0) == ""
    assert px_terminal.crop_ansi_string_at_length("", 4) == ""
    assert px_terminal.crop_ansi_string_at_length("1234", 4) == "1234"
    assert px_terminal.crop_ansi_string_at_length("1234", 3) == "123"
    assert px_terminal.crop_ansi_string_at_length("1234", 5) == "1234"

    bold_end = u"1234" + px_terminal.bold("5678")
    assert px_terminal.crop_ansi_string_at_length(bold_end, 3) == "123"
    assert px_terminal.crop_ansi_string_at_length(bold_end, 4) == "1234"

    # Note that we expect the string cutter to add an end-marker when
    # breaking inside a formatted section
    assert px_terminal.crop_ansi_string_at_length(bold_end, 5) == \
        u"1234[1m5[0m".replace('[', CSI)

    assert px_terminal.crop_ansi_string_at_length(bold_end, 8) == \
        u"1234[1m5678[0m".replace('[', CSI)

    bold_middle = u"123" + px_terminal.bold("456") + u"789"
    assert px_terminal.crop_ansi_string_at_length(bold_middle, 6) == \
        u"123[1m456[0m".replace('[', CSI)
    assert px_terminal.crop_ansi_string_at_length(bold_middle, 7) == \
        u"123[1m456[22m7[0m".replace('[', CSI)


def test_getch():
    pipe = os.pipe()
    read, write = pipe
    os.write(write, b'q')

    # We should get unicode responses from getch()
    sequence = px_terminal.getch(timeout_seconds=0, fd=read)
    assert sequence is not None
    assert sequence._string == u'q'


def test_tokenize():
    input = u"ab" + px_terminal.bold(u"c") + u"de"
    parts = []  # type: List[text_type]
    for token in px_terminal._tokenize(input):
        parts.append(token)

    assert parts == [
        'ab',
        '\x1b[1m',
        'c',
        '\x1b[22m',
        'de'
    ]