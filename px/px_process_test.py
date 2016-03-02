import getpass

import os
import px_process


def test_create_process():
    process_builder = px_process.PxProcessBuilder()
    process_builder.pid = 7
    process_builder.username = "usernamex"
    process_builder.cpu_time = 1.3
    process_builder.memory_percent = 42.7
    process_builder.cmdline = "hej kontinent"
    test_me = px_process.PxProcess(process_builder)

    assert test_me.pid == 7
    assert test_me.user == "usernamex"
    assert test_me.cpu_time_s == "1.300s"
    assert test_me.memory_percent_s == "43%"
    assert test_me.cmdline == "hej kontinent"


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


def test_ps_line_to_process():
    process = px_process.ps_line_to_process(
        "47536 root              0:00.03  0.0 /usr/sbin/cupsd -l"
    )

    assert process.pid == 47536
    assert process.user == "root"
    assert process.cpu_time_s == "0.030s"
    assert process.memory_percent_s == "0%"
    assert process.cmdline == "/usr/sbin/cupsd -l"


def test_get_all():
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
