import datetime

import dateutil.tz


def get_users_at(last_output, now, testtime):
    """
    Ask px_loginhistory to parse last_output given the current timestamp of now.

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


def test_get_users_at_until_crash():
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan     ttys001                   Thu Nov 26 19:55 - crash (27+07:11)"

    # Before
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2015, 11, 26, 19, 54, tzinfo=dateutil.tz.tzlocal()))

    # During
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2015, 11, 26, 19, 55, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2015, 12, 10, 19, 53, tzinfo=dateutil.tz.tzlocal()))

    # A bit after
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2015, 12, 26, 19, 55, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_until_shutdown():
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "_mbsetupuser  console                   Mon Jan 18 20:31 - shutdown (34+01:29)"

    # Before
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 01, 18, 20, 30, tzinfo=dateutil.tz.tzlocal()))

    # During
    assert set(["_mbsetupuser"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 01, 18, 20, 31, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 02, 18, 20, 30, tzinfo=dateutil.tz.tzlocal()))

    # A bit after
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 02, 28, 20, 30, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_multiple():
    # Test multiple users logged in between two timestamps
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "\n".join([
        "johan1     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
        "johan2     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
    ])

    # Before
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 31, 14, 38, tzinfo=dateutil.tz.tzlocal()))

    # During
    assert set(["johan1", "johan2"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 31, 14, 39, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan1", "johan2"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 31, 17, 46, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan1", "johan2"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 01, 11, 8, tzinfo=dateutil.tz.tzlocal()))

    # After
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 01, 11, 9, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_pseudousers_osx():
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())

    # Note trailing space in test string, we get that from last on OS X 10.11.3
    lastline = "reboot    ~                         Fri Oct 23 06:50 "
    # "reboot" is not a real user, it shouldn't be listed
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2015, 10, 23, 06, 50, tzinfo=dateutil.tz.tzlocal()))

    # Note trailing space in test string, we get that from last on OS X 10.11.3
    lastline = "shutdown  ~                         Fri Oct 23 06:49 "
    # "shutdown" is not a real user, it shouldn't be listed
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2015, 10, 23, 06, 49, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_pseudousers_linux():
    # FIXME: Test reboot pseudo user on Linux

    # FIXME: Test shutdown pseudo user on Linux
    pass
