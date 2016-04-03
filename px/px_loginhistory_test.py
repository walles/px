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
    assert not get_users_at(
        "johan     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
        datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal()),
        datetime.datetime(2016, 03, 31, 14, 38, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        "johan     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
        datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal()),
        datetime.datetime(2016, 03, 31, 14, 39, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        "johan     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
        datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal()),
        datetime.datetime(2016, 03, 31, 17, 46, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        "johan     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
        datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal()),
        datetime.datetime(2016, 04, 01, 11, 8, tzinfo=dateutil.tz.tzlocal()))
    assert not get_users_at(
        "johan     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
        datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal()),
        datetime.datetime(2016, 04, 01, 11, 9, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_still_logged_in():
    # FIXME: Test user still logged in
    pass


def test_get_users_at_remote():
    # FIXME: Test user logged in remotely
    pass


def test_get_users_at_local():
    # FIXME: Test user logged in locally
    pass


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
