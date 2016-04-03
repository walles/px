import datetime

import dateutil.tz


def get_users_at(last_string, now, testtime):
    """
    Ask px_loginhistory to parse last_string given the current timestamp of now.

    Then return the users px_loginhistory claims were logged in at testtime.
    """
    return None


def test_get_users_at_range():
    # Test user logged in between two timestamps
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)"

    # Before
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 31, 14, 38, tzinfo=dateutil.tz.tzlocal()))

    # During
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 31, 14, 39, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 31, 17, 46, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 01, 11, 8, tzinfo=dateutil.tz.tzlocal()))

    # After
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 01, 11, 9, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_still_logged_in():
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan     ttys000                   Sun Apr  3 11:54   still logged in"

    # Before
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 03, 11, 53, tzinfo=dateutil.tz.tzlocal()))

    # During
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 03, 11, 54, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime.now(dateutil.tz.tzlocal()))


def test_get_users_at_remote():
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "root     pts/1        10.1.6.120       Tue Jan 28 05:59   still logged in"

    assert set(["root from 10.1.6.120"]) == get_users_at(
        lastline, now,
        datetime.datetime.now(dateutil.tz.tzlocal()))


def test_get_users_at_local():
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan     ttys000                   Sun Apr  3 11:54   still logged in"

    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime.now(dateutil.tz.tzlocal()))


def test_get_users_at_until_event():
    # FIXME: Test user logged in until crash

    # FIXME: Test user logged in until shutdown
    pass


def test_get_users_at_pseudousers_linux():
    # FIXME: Test reboot pseudo user on Linux

    # FIXME: Test shutdown pseudo user on Linux
    pass


def test_get_users_at_pseudousers_osx():
    # FIXME: Test reboot pseudo user on OS X

    # FIXME: Test shutdown pseudo user on OS X
    pass
