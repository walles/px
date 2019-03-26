from . import testutils

from px import px_cwdfriends


def test_current_cwd_unknown():
    test_me = px_cwdfriends.PxCwdFriends(123, [], [])
    assert test_me.cwd is None
    assert test_me.friends == []


def test_current_cwd_root():
    process = testutils.create_process(pid=123)
    cwd_file = testutils.create_file("cwd", "/", None, 123)
    test_me = px_cwdfriends.PxCwdFriends(123, [process], [cwd_file])
    assert test_me.cwd == '/'
    assert test_me.friends == []


def test_current_cwd_notroot():
    process = testutils.create_process(pid=123)
    cwd_file = testutils.create_file("cwd", "/notroot", None, 123)
    test_me = px_cwdfriends.PxCwdFriends(123, [process], [cwd_file])

    print(test_me.cwd)

    assert test_me.cwd == '/notroot'
    assert test_me.friends == []
