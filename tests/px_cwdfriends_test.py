from . import testutils

from px import px_cwdfriends

from typing import List
from px import px_process


def test_current_cwd_unknown():
    process = testutils.create_process()
    test_me = px_cwdfriends.PxCwdFriends(process, [], [])
    assert test_me.cwd is None
    assert test_me.friends == []


def test_current_cwd_root():
    process = testutils.create_process(pid=123)
    cwd_file = testutils.create_file("xxx", "/", None, 123, fdtype="cwd")
    test_me = px_cwdfriends.PxCwdFriends(process, [process], [cwd_file])
    assert test_me.cwd == "/"
    assert test_me.friends == []


def test_current_cwd_notroot():
    process = testutils.create_process(pid=123)
    cwd_file = testutils.create_file("xxx", "/notroot", None, 123, fdtype="cwd")
    test_me = px_cwdfriends.PxCwdFriends(process, [process], [cwd_file])
    assert test_me.cwd == "/notroot"
    assert test_me.friends == []


def test_find_friends():
    process = testutils.create_process(pid=123)
    friend = testutils.create_process(pid=234)
    notfriend1 = testutils.create_process(pid=666)
    notfriend2 = testutils.create_process(pid=667)

    cwd_file = testutils.create_file("xxx", "/notroot", None, 123, fdtype="cwd")
    friend_cwd = testutils.create_file("xxx", "/notroot", None, 234, fdtype="cwd")
    notfriend_cwd = testutils.create_file(
        "xxx", "/somewhereelse", None, 666, fdtype="cwd"
    )
    # notfriend2 cwd intentionally left blank for the sake of this test

    test_me = px_cwdfriends.PxCwdFriends(
        process,
        [process, friend, notfriend1, notfriend2],
        [cwd_file, friend_cwd, notfriend_cwd],
    )

    assert test_me.cwd == "/notroot"
    assert test_me.friends == [friend]


def _get_friends_in_order(*args: str) -> List[str]:
    procs = []
    files = []
    for index, arg in enumerate(args):
        procs.append(testutils.create_process(pid=index, commandline=arg))
        files.append(testutils.create_file("xxx", "yyy", None, index, fdtype="cwd"))

    me = testutils.create_process(pid=1234, commandline="base-process")
    procs.append(me)
    files.append(testutils.create_file("xxx", "yyy", None, me.pid, fdtype="cwd"))

    return_me = []
    for friend in px_cwdfriends.PxCwdFriends(me, procs, files).friends:
        return_me.append(friend.cmdline)

    return return_me


def _get_friend_processes_in_order(
    *args: px_process.PxProcess,
) -> List[px_process.PxProcess]:
    files = []
    procs = list(args)
    for proc in procs:
        files.append(testutils.create_file("xxx", "yyy", None, proc.pid, fdtype="cwd"))

    me = testutils.create_process(pid=1234, commandline="base-process")
    procs.append(me)
    files.append(testutils.create_file("xxx", "yyy", None, me.pid, fdtype="cwd"))

    return px_cwdfriends.PxCwdFriends(me, procs, files).friends


def test_friend_ordering():
    # Test alphabetic order
    assert _get_friends_in_order("a", "b") == ["a", "b"]
    assert _get_friends_in_order("b", "a") == ["a", "b"]

    # Test ignoring initial -
    assert _get_friends_in_order("a", "-b", "c") == ["a", "-b", "c"]

    # Test PID as secondary key
    p1 = testutils.create_process(pid=1, commandline="a")
    p2 = testutils.create_process(pid=2, commandline="a")
    assert _get_friend_processes_in_order(p1, p2) == [p1, p2]
    assert _get_friend_processes_in_order(p2, p1) == [p1, p2]
