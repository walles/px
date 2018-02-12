import getpass

import os
import six
import pytest

from px import px_process
from . import testutils

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import MutableSet  # NOQA


def test_create_process():
    process_builder = px_process.PxProcessBuilder()
    process_builder.pid = 7
    process_builder.ppid = 1
    process_builder.start_time_string = testutils.TIMESTRING
    process_builder.username = "usernamex"
    process_builder.cpu_time = 1.3
    process_builder.memory_percent = 42.7
    process_builder.cmdline = "hej kontinent"
    test_me = px_process.PxProcess(process_builder, testutils.now())

    assert test_me.pid == 7
    assert test_me.ppid == 1
    assert test_me.username == "usernamex"
    assert test_me.cpu_time_s == "1.3s"
    assert test_me.memory_percent_s == "43%"
    assert test_me.cmdline == "hej kontinent"

    assert test_me.start_time == testutils.TIME
    assert test_me.age_seconds > 0


def test_call_ps():
    lines = list(px_process.call_ps())

    # There should be at least 20 processes running on any single system. If
    # there's a counter example, we'll just have to lower the 20 and document
    # the counter example.
    assert len(lines) > 20

    for line in lines:
        # 20 is an arbitrary lowest limit, if there are cases where this test
        # fails even though it shouldn't, just document the reason here and
        # lower the limit
        assert len(line) > 20

        # We want these lines to be unicode, this is needed if we have unicode
        # chars in command lines
        assert isinstance(line, six.text_type)

    assert "COMMAND" not in lines[0]


def test_ps_line_to_process_unicode():
    process = testutils.create_process(cputime="2:14.15")

    assert process.username == u"root"
    assert process.cmdline == u"/usr/sbin/cupsd -l"


def test_ps_line_to_process_1():
    process = testutils.create_process()

    assert process.pid == 47536
    assert process.ppid == 1234
    assert process.username == "root"
    assert process.cpu_time_s == "0.03s"
    assert process.memory_percent_s == "0%"
    assert process.cmdline == "/usr/sbin/cupsd -l"

    assert process.start_time == testutils.TIME
    assert process.age_seconds > 0


def test_ps_line_to_process_2():
    process = testutils.create_process(cputime="2:14.15")

    assert process.pid == 47536
    assert process.ppid == 1234
    assert process.username == "root"
    assert process.cpu_time_s == "2m14s"
    assert process.memory_percent_s == "0%"
    assert process.cmdline == "/usr/sbin/cupsd -l"

    assert process.start_time == testutils.TIME
    assert process.age_seconds > 0


# From a real-world failure
def test_ps_line_to_process_3():
    process = px_process.ps_line_to_process(
        "  5328"
        "   4432"
        " Thu Feb 25 07:42:36 2016"
        " " + str(os.getuid()) +
        "    1-19:31:31"
        " 19.7"
        " /usr/sbin/mysqld"
        " --basedir=/usr"
        " --datadir=/data/user/mysql"
        " --plugin-dir=/usr/lib/mysql/plugin"
        " --user=mysql"
        " --log-error=/var/log/mysql/mysql.err"
        " --pid-file=/var/run/mysqld/mysqld.pid"
        " --socket=/var/run/mysqld/mysqld.sock"
        " --port=3306", testutils.now())
    assert process.username == getpass.getuser()
    assert process.memory_percent_s == "20%"
    assert process.cpu_time_s == "1d19h"
    assert process.command == "mysqld"


def _validate_references(processes):
    """Fsck the parent / children relationships between all processes"""
    for process in processes:
        if process.pid == 0:
            assert process.parent is None
        else:
            assert process.parent is not None

        assert type(process.children) is set
        if process.parent:
            assert process.parent in processes
            assert process in process.parent.children

        for child in process.children:
            assert child in processes
            assert child.parent == process


def _test_get_all():
    all = px_process.get_all()
    assert len(all) >= 4  # Expect at least kernel, init, bash and python
    for process in all:
        assert process is not None

    pids = list(map(lambda p: p.pid, all))

    # Finding ourselves is just confusing...
    assert os.getpid() not in pids

    # ... but all other processes should be there
    assert os.getppid() in pids

    # PID 1 is launchd on OS X, init on Linux.
    #
    # If there's a system where PID 1 doesn't exist this test needs to be modded
    # and that system documented here.
    assert 1 in pids

    # Assert that all contains no duplicate PIDs
    seen_pids = set()  # type: MutableSet[int]
    for process in all:
        pid = process.pid
        assert pid not in seen_pids
        seen_pids.add(pid)

    # Assert that there are processes with the current user name
    current_users_processes = (
        filter(lambda process: process.username == getpass.getuser(), all))
    assert current_users_processes

    _validate_references(all)

    now = testutils.now()
    for process in all:
        # Scores should be computed via multiplications and divisions of
        # positive numbers, if this value is negative something is wrong.
        assert process.score >= 0

        # Processes created in the future = fishy
        assert process.age_seconds >= 0
        assert process.start_time < now

    for process in all:
        assert isinstance(process.cmdline, six.text_type)
        assert isinstance(process.username, six.text_type)


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
    p0 = testutils.create_process(cputime="0:10.00", mempercent="10.0")
    p1 = testutils.create_process(commandline="awk", cputime="0:11.00", mempercent="1.0")
    p2 = testutils.create_process(commandline="bash", cputime="0:01.00", mempercent="11.0")

    # P0 should be last because its score is the highest, and p1 and p2 should
    # be ordered alphabetically
    assert px_process.order_best_last([p0, p1, p2]) == [p1, p2, p0]
    assert px_process.order_best_last([p2, p1, p0]) == [p1, p2, p0]


def test_order_best_first():
    p0 = testutils.create_process(cputime="0:10.00", mempercent="10.0")
    p1 = testutils.create_process(commandline="awk", cputime="0:11.00", mempercent="1.0")
    p2 = testutils.create_process(commandline="bash", cputime="0:01.00", mempercent="11.0")

    # P0 should be first because its score is the highest, then p1 and p2 should
    # be ordered alphabetically
    assert px_process.order_best_first([p0, p1, p2]) == [p0, p1, p2]
    assert px_process.order_best_first([p2, p1, p0]) == [p0, p1, p2]


def test_match():
    p = testutils.create_process(uid=0, commandline="/usr/libexec/AirPlayXPCHelper")

    assert p.match(None)

    assert p.match("root")
    assert not p.match("roo")

    assert p.match("Air")
    assert p.match("Play")

    assert p.match("air")
    assert p.match("play")


def test_seconds_to_str():
    assert px_process.seconds_to_str(0.54321) == "0.54s"
    assert px_process.seconds_to_str(1.54321) == "1.54s"
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
    p = testutils.create_process(commandline="/usr/libexec/AirPlayXPCHelper")
    assert p.get_command_line_array() == ["/usr/libexec/AirPlayXPCHelper"]

    p = testutils.create_process(commandline="/usr/sbin/universalaccessd launchd -s")
    assert p.get_command_line_array() == ["/usr/sbin/universalaccessd", "launchd", "-s"]


def test_get_command_line_array_space_in_binary(tmpdir):
    # Create a file name with a space in it
    spaced_path = tmpdir.join("i contain spaces")
    spaced_path.write_binary(b"")
    spaced_name = str(spaced_path)

    # Verify splitting of the spaced file name
    p = testutils.create_process(commandline=spaced_name)
    assert p.get_command_line_array() == [spaced_name]

    # Verify splitting with more parameters on the line
    p = testutils.create_process(commandline=spaced_name + " parameter")
    assert p.get_command_line_array() == [spaced_name, "parameter"]


def test_command_dotted_prefix():
    # If there's a dot with a lot of text after it we should drop everything
    # before the dot.
    p = testutils.create_process(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService")
    assert p.command == "TextReplacementService"

    # If there's a dot with four characters or less after it, assume it's a file
    # suffix and take the next to last section
    p = testutils.create_process(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService.1234")
    assert p.command == "TextReplacementService"
    p = testutils.create_process(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService.12345")
    assert p.command == "12345"


def test_command_linux_kernelproc():
    p = testutils.create_process(commandline="[ksoftirqd/0]")
    assert p.command == "[ksoftirqd/0]"

    p = testutils.create_process(commandline="[kworker/0:0H]")
    assert p.command == "[kworker/0:0H]"

    p = testutils.create_process(commandline="[rcuob/3]")
    assert p.command == "[rcuob/3]"


def test_command_in_parentheses():
    # Observed on OS X
    p = testutils.create_process(commandline="(python2.7)")
    assert p.command == "(python2.7)"


def test_uid_to_username():
    username = px_process.uid_to_username(os.getuid())
    assert username == getpass.getuser()
    assert isinstance(username, six.text_type)

    username = px_process.uid_to_username(456789)
    assert username == "456789"
    assert isinstance(username, six.text_type)
