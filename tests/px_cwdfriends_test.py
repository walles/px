from . import testutils

from px import px_cwdfriends


def test_current_cwd_unknown():
    process = testutils.create_process()
    test_me = px_cwdfriends.PxCwdFriends(process, [], [])
    assert test_me.cwd is None
    assert test_me.friends == []


def test_current_cwd_root():
    process = testutils.create_process(pid=123)
    cwd_file = testutils.create_file("cwd", "/", None, 123)
    test_me = px_cwdfriends.PxCwdFriends(process, [process], [cwd_file])
    assert test_me.cwd == '/'
    assert test_me.friends == []


def test_current_cwd_notroot():
    process = testutils.create_process(pid=123)
    cwd_file = testutils.create_file("cwd", "/notroot", None, 123)
    test_me = px_cwdfriends.PxCwdFriends(process, [process], [cwd_file])
    assert test_me.cwd == '/notroot'
    assert test_me.friends == []


def test_find_friends():
    process = testutils.create_process(pid=123)
    friend = testutils.create_process(pid=234)
    notfriend1 = testutils.create_process(pid=666)
    notfriend2 = testutils.create_process(pid=667)

    cwd_file = testutils.create_file("cwd", "/notroot", None, 123)
    friend_cwd = testutils.create_file("cwd", "/notroot", None, 234)
    notfriend_cwd = testutils.create_file("cwd", "/somewhereelse", None, 666)
    # notfriend2 cwd intentionally left blank for the sake of this test

    test_me = px_cwdfriends.PxCwdFriends(
        process,
        [process, friend, notfriend1, notfriend2],
        [cwd_file, friend_cwd, notfriend_cwd])

    assert test_me.cwd == '/notroot'
    assert test_me.friends == [friend]
