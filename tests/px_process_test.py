import getpass
import datetime

import os
import pytest

from px import px_process
from . import testutils

from typing import MutableSet


def test_create_process():
    process_builder = px_process.PxProcessBuilder()
    process_builder.pid = 7
    process_builder.ppid = 1
    process_builder.rss_kb = 123
    process_builder.start_time_string = testutils.TIMESTRING
    process_builder.username = "usernamex"
    process_builder.cpu_time = 1.3
    process_builder.memory_percent = 42.7
    process_builder.cmdline = "hej kontinent"
    test_me = process_builder.build(testutils.local_now())

    assert test_me.pid == 7
    assert test_me.ppid == 1
    assert test_me.rss_kb == 123
    assert test_me.username == "usernamex"
    assert test_me.cpu_time_s == "1.3s"
    assert test_me.memory_percent_s == "43%"
    assert test_me.cmdline == "hej kontinent"

    assert test_me.start_time == testutils.TIME
    assert test_me.age_seconds > 0


def test_create_future_process():
    """
    Handle the case where we first look at the clock, then list processes.

    Let's say that:
    1. We look at the clock, and the clock is 12:34:56
    2. We find a newly started process at     12:34:57

    This case used to lead to crashes when we asserted for this:
    https://github.com/walles/px/issues/84
    """
    process_builder = px_process.PxProcessBuilder()

    # This is what we want to test
    process_builder.start_time_string = testutils.TIMESTRING
    before_the_process_was_started = testutils.TIME - datetime.timedelta(seconds=1)

    # These values are required to not fail in other ways
    process_builder.cmdline = "hej kontinent"
    process_builder.pid = 1
    process_builder.rss_kb = 123
    process_builder.username = "johan"

    # Test it!
    test_me = process_builder.build(before_the_process_was_started)
    assert test_me.age_seconds == 0


def test_ps_line_to_process_unicode():
    process = testutils.create_process(cputime="2:14.15")

    assert process.username == "root"
    assert process.cmdline == "/usr/sbin/cupsd -l"


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
        "   123"
        " Thu Feb 25 07:42:36 2016"
        " " + str(os.getuid()) + " 5.5"
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
        " --port=3306",
        testutils.local_now(),
    )
    assert process.username == getpass.getuser()
    assert process.cpu_percent_s == "6%"
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

        assert isinstance(process.children, list)
        if process.parent:
            assert process.parent in processes
            assert process.parent.pid == process.ppid
            assert process in process.parent.children

        for child in process.children:
            assert child in processes
            assert child.parent == process


def _test_get_all():
    all_processes = px_process.get_all()
    assert len(all_processes) >= 4  # Expect at least kernel, init, bash and python
    for process in all_processes:
        assert process is not None

    pids = list(map(lambda p: p.pid, all_processes))

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
    seen_pids: MutableSet[int] = set()
    for process in all_processes:
        pid = process.pid
        assert pid not in seen_pids
        seen_pids.add(pid)

    # Assert that there are processes with the current user name
    current_users_processes = filter(
        lambda process: process.username == getpass.getuser(), all_processes
    )
    assert current_users_processes

    _validate_references(all_processes)

    for process in all_processes:
        assert isinstance(process.cmdline, str)
        assert isinstance(process.username, str)

    if os.environ.get("CI") == "true":
        # Checking for future processes sometimes fails in CI. Since I don't
        # understand it and can't fix it, let's just not look for that in CI. If
        # it happens locally, then that's a good start for troupleshooting.
        #
        # For reference, in
        # https://github.com/Homebrew/homebrew-core/pull/186101 four different
        # runs of "macOS 14-arm64" failed like this, all with processes created
        # around 100s-210s in the future.
        return

    # Ensure no processes are from the future
    now = testutils.local_now()
    for process in all_processes:
        # Processes created in the future = fishy
        assert process.age_seconds >= 0
        assert process.start_time < now


def test_get_all_swedish():
    """
    In Swedish, floating point numbers are indicated with comma, so 4.2 in
    English is 4,2 in Swedish. This test verifies that setting a Swedish locale
    won't mess up our parsing.
    """
    os.environ["LANG"] = "sv_SE.UTF-8"
    os.environ["LC_TIME"] = "sv_SE.UTF-8"
    os.environ["LC_NUMERIC"] = "sv_SE.UTF-8"

    _test_get_all()


def test_get_all_defaultlocale():
    del os.environ["LANG"]
    _test_get_all()


def test_process_eq():
    """Compare two mostly identical processes, where one has a parent and the other one not"""
    process_a = testutils.create_process()

    process_b = testutils.create_process()
    parent = px_process.create_kernel_process(testutils.local_now())
    process_b.parent = parent

    assert process_a != process_b


def test_parse_time():
    assert px_process.parse_time("0:00.03") == 0.03
    assert px_process.parse_time("1:02.03") == 62.03
    assert px_process.parse_time("03:35:32") == 3 * 60 * 60 + 35 * 60 + 32
    assert px_process.parse_time("9-03:35:32") == 9 * 86400 + 3 * 60 * 60 + 35 * 60 + 32

    with pytest.raises(ValueError) as e:
        px_process.parse_time("Constantinople")
    assert "Constantinople" in str(e.value)


def test_match():
    p = testutils.create_process(uid=0, commandline="/usr/libexec/AirPlayXPCHelper")

    assert p.match(None)

    assert p.match("root")
    assert not p.match("roo")

    assert p.match("Air")
    assert p.match("Play")

    assert p.match("air")
    assert p.match("play")

    # Match PID by prefix but not substring. Exact matches are used for
    # searching in ptop. Prefix matching is used to not throw the right answer
    # away while the user is typing their search in ptop. Substring matching has
    # no value.
    assert p.match("47536")
    assert p.match("4753")
    assert not p.match("7536")


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
        commandline="/.../com.apple.InputMethodKit.TextReplacementService"
    )
    assert p.command == "TextReplacementService"

    # If there's a dot with four characters or less after it, assume it's a file
    # suffix and take the next to last section
    p = testutils.create_process(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService.1234"
    )
    assert p.command == "TextReplacementService"
    p = testutils.create_process(
        commandline="/.../com.apple.InputMethodKit.TextReplacementService.12345"
    )
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
    assert isinstance(username, str)

    username = px_process.uid_to_username(456789)
    assert username == "456789"
    assert isinstance(username, str)


def test_resolve_links():
    UNKNOWN_PID = 1323532
    p1 = testutils.create_process(pid=1, ppid=UNKNOWN_PID)
    p2 = testutils.create_process(pid=2, ppid=1)
    processes = {p1.pid: p1, p2.pid: p2}
    px_process.resolve_links(processes, testutils.local_now())

    assert p1.parent is None
    assert p2.parent is p1

    # Verify both equality...
    assert p1.children == [p2]
    # ... and identity of the child.
    assert list(p1.children)[0] is p2


def test_resolve_links_multiple_roots():
    """There can be only one. Root. Of the process tree."""
    processes = px_process.get_all()
    process_map = {p.pid: p for p in processes}
    px_process.resolve_links(process_map, testutils.local_now())

    root0 = processes[0]
    while root0.parent:
        root0 = root0.parent

    for process in processes:
        root = process
        while root.parent:
            root = root.parent

        assert root is root0
