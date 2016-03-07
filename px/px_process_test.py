import random
import getpass
import datetime

import os
import pytest
import px_process
import dateutil.parser


# An example time string that can be produced by ps
TIMESTRING = "Mon Mar 7 09:33:11 2016"
TIME = dateutil.parser.parse(TIMESTRING)
SECONDS_SINCE_EPOCH = (TIME - datetime.datetime(1970, 1, 1)).total_seconds()


def test_create_process():
    process_builder = px_process.PxProcessBuilder()
    process_builder.pid = 7
    process_builder.ppid = 1
    process_builder.start_time_string = TIMESTRING
    process_builder.username = "usernamex"
    process_builder.cpu_time = 1.3
    process_builder.memory_percent = 42.7
    process_builder.cmdline = "hej kontinent"
    test_me = px_process.PxProcess(process_builder)

    assert test_me.pid == 7
    assert test_me.ppid == 1
    assert test_me.username == "usernamex"
    assert test_me.cpu_time_s == "1.3s"
    assert test_me.memory_percent_s == "43%"
    assert test_me.cmdline == "hej kontinent"

    time = dateutil.parser.parse(TIMESTRING)
    assert time.year == 2016
    assert test_me.start_seconds_since_epoch == SECONDS_SINCE_EPOCH


def test_call_ps():
    lines = px_process.call_ps()

    # There should be at least 20 processes running on any single system. If
    # there's a counter example, we'll just have to lower the 20 and document
    # the counter example.
    assert len(lines) > 20

    for line in lines:
        # 20 is an arbitrary lowest limit, if there are cases where this test
        # fails even though it shouldn't, just document the reason here and
        # lower the limit
        assert len(line) > 20

    assert "COMMAND" not in lines[0]


def spaces(at_least=1, at_most=3):
    return " " * random.randint(at_least, at_most)


def psline(pid=47536, ppid=1234,
           timestring=TIMESTRING,
           username="root",
           cputime="0:00.03", mempercent="0.0",
           commandline="/usr/sbin/cupsd -l"):

    return (spaces(at_least=0) +
            str(pid) + spaces() +
            str(ppid) + spaces() +
            timestring + spaces() +
            username + spaces() +
            cputime + spaces() +
            mempercent + spaces() +
            commandline)


def test_ps_line_to_process_1():
    process = px_process.ps_line_to_process(psline())

    assert process.pid == 47536
    assert process.ppid == 1234
    assert process.username == "root"
    assert process.cpu_time_s == "0.03s"
    assert process.memory_percent_s == "0%"
    assert process.cmdline == "/usr/sbin/cupsd -l"
    assert process.start_seconds_since_epoch == SECONDS_SINCE_EPOCH


def test_ps_line_to_process_2():
    process = px_process.ps_line_to_process(psline(cputime="2:14.15"))

    assert process.pid == 47536
    assert process.ppid == 1234
    assert process.username == "root"
    assert process.cpu_time_s == "2m14s"
    assert process.memory_percent_s == "0%"
    assert process.cmdline == "/usr/sbin/cupsd -l"
    assert process.start_seconds_since_epoch == SECONDS_SINCE_EPOCH


def _validate_references(processes):
    """Fsck the parent / children relationships between all processes"""
    for process in processes:
        if process.pid == 0:
            assert process.parent is None
        else:
            assert process.parent is not None

        assert type(process.children) is set
        if process.parent:
            assert process in process.parent.children

        for child in process.children:
            assert child.parent == process


def _test_get_all():
    all = px_process.get_all()

    pids = map(lambda p: p.pid, all)
    assert os.getpid() in pids

    # PID 1 is launchd on OS X, init on Linux.
    #
    # If there's a system where PID 1 doesn't exist this test needs to be modded
    # and that system documented here.
    assert 1 in pids

    # Assert that all contains no duplicate PIDs
    seen_pids = set()
    for process in all:
        pid = process.pid
        assert pid not in seen_pids
        seen_pids.add(pid)

    # Assert that the current PID has the correct user name
    current_process = filter(lambda process: process.pid == os.getpid(), all)[0]
    assert current_process.username == getpass.getuser()

    _validate_references(all)


def test_get_all_swedish():
    """
    In Swedish, floating point numbers are indicated with comma, so 4.2 in
    English is 4,2 in Swedish. This test verifies that setting a Swedish locale
    won't mess up our parsing.
    """
    os.environ["LANG"] = "sv_SE.UTF-8"
    _test_get_all()


def test_get_all_defaultlocale():
    del os.environ["LANG"]
    _test_get_all()


def test_parse_time():
    assert px_process.parse_time("0:00.03") == 0.03
    assert px_process.parse_time("1:02.03") == 62.03
    assert px_process.parse_time("03:35:32") == 3 * 60 * 60 + 35 * 60 + 32
    assert px_process.parse_time("9-03:35:32") == 9 * 86400 + 3 * 60 * 60 + 35 * 60 + 32

    with pytest.raises(ValueError) as e:
        px_process.parse_time("Constantinople")
    assert "Constantinople" in str(e.value)


def test_order_best_last():
    # Verify ordering by score
    p0 = px_process.ps_line_to_process(psline(cputime="0:10.00", mempercent="10.0"))
    p1 = px_process.ps_line_to_process(psline(cputime="0:11.00", mempercent="1.0"))
    p2 = px_process.ps_line_to_process(psline(cputime="0:01.00", mempercent="11.0"))
    ordered = px_process.order_best_last([p0, p1, p2])

    # The first process should have the highest CPU*Memory score, and should
    # therefore be ordered last
    assert ordered[2] == p0

    # Verify ordering same-scored processes by command line
    p0 = px_process.ps_line_to_process(psline(commandline="awk"))
    p1 = px_process.ps_line_to_process(psline(commandline="bash"))
    assert px_process.order_best_last([p0, p1]) == [p0, p1]
    assert px_process.order_best_last([p1, p0]) == [p0, p1]


def test_match():
    p = px_process.ps_line_to_process(
        psline(username="root", commandline="/usr/libexec/AirPlayXPCHelper"))

    assert p.match(None)

    assert p.match("root")
    assert not p.match("roo")

    assert p.match("Air")
    assert p.match("Play")

    assert p.match("air")
    assert p.match("play")


def test_seconds_to_str():
    assert px_process.seconds_to_str(0.54321) == "0.543s"
    assert px_process.seconds_to_str(0.5) == "0.5s"
    assert px_process.seconds_to_str(1.0) == "1.0s"
    assert px_process.seconds_to_str(1) == "1s"

    assert px_process.seconds_to_str(60.54321) == "1m00s"

    assert px_process.seconds_to_str(3598.54321) == "59m58s"
    assert px_process.seconds_to_str(3659.54321) == "1h00m"
    assert px_process.seconds_to_str(3660.54321) == "1h01m"
    assert px_process.seconds_to_str(4260.54321) == "1h11m"

    t1h = 3600
    t1d = t1h * 24
    assert px_process.seconds_to_str(t1d + 3598) == "1d00h"
    assert px_process.seconds_to_str(t1d + 3659) == "1d01h"
    assert px_process.seconds_to_str(t1d + t1h * 11) == "1d11h"


def test_get_command_line_array():
    p = px_process.ps_line_to_process(psline(commandline="/usr/libexec/AirPlayXPCHelper"))
    assert p.get_command_line_array() == ["/usr/libexec/AirPlayXPCHelper"]

    p = px_process.ps_line_to_process(psline(commandline="/usr/sbin/universalaccessd launchd -s"))
    assert p.get_command_line_array() == ["/usr/sbin/universalaccessd", "launchd", "-s"]


def test_get_command_line_array_space_in_binary(tmpdir):
    # Create a file name with a space in it
    spaced_path = tmpdir.join("i contain spaces")
    spaced_path.write_binary("")
    spaced_name = str(spaced_path)

    # Verify splitting of the spaced file name
    p = px_process.ps_line_to_process(psline(commandline=spaced_name))
    assert p.get_command_line_array() == [spaced_name]

    # Verify splitting with more parameters on the line
    p = px_process.ps_line_to_process(psline(commandline=spaced_name + " parameter"))
    assert p.get_command_line_array() == [spaced_name, "parameter"]


def test_command_dotted_prefix():
    # If there's a dot with a lot of text after it we should drop everything
    # before the dot.
    p = px_process.ps_line_to_process(psline(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService"))
    assert p.command == "TextReplacementService"

    # If there's a dot with four characters or less after it, assume it's a file
    # suffix and take the next to last section
    p = px_process.ps_line_to_process(psline(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService.1234"))
    assert p.command == "TextReplacementService"
    p = px_process.ps_line_to_process(psline(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService.12345"))
    assert p.command == "12345"
