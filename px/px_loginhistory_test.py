import datetime

import pytest
import dateutil.tz
import px_loginhistory


@pytest.yield_fixture
def check_output(capfd):
    yield None

    out, err = capfd.readouterr()
    assert not err


def get_users_at(last_output, now, testtime):
    """
    Ask px_loginhistory to parse last_output given the current timestamp of now.

    Then return the users px_loginhistory claims were logged in at testtime.
    """
    return px_loginhistory.get_users_at(testtime, last_output=last_output, now=now)


def test_get_users_at_range(check_output):
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


def test_get_users_at_still_logged_in(check_output):
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


def test_get_users_at_remote(check_output):
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "root     pts/1        10.1.6.120       Tue Jan 28 05:59   still logged in"

    assert set(["root from 10.1.6.120"]) == get_users_at(
        lastline, now,
        datetime.datetime.now(dateutil.tz.tzlocal()))


def test_get_users_at_local_osx(check_output):
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan     ttys000                   Sun Apr  3 11:54   still logged in"

    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime.now(dateutil.tz.tzlocal()))


def test_get_users_at_local_linux(check_output):
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan    pts/2        :0               Wed Mar  9 13:25 - 13:38  (00:12)"

    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 9, 13, 26, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_until_crash(check_output):
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


def test_get_users_at_until_shutdown_osx(check_output):
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
    assert set(["_mbsetupuser"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 02, 18, 20, 30, tzinfo=dateutil.tz.tzlocal()))

    # A bit after
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 02, 28, 20, 30, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_until_shutdown_linux(check_output):
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan    :0           :0               Sat Mar 26 22:04 - down   (00:08)"

    # Before
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 26, 22, 03, tzinfo=dateutil.tz.tzlocal()))

    # During
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 26, 22, 04, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 26, 22, 9, tzinfo=dateutil.tz.tzlocal()))

    # A bit after
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 26, 22, 15, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_multiple(check_output):
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


def test_get_users_at_pseudousers_osx(check_output):
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


def test_get_users_at_pseudousers_linux(check_output):
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())

    lastline = "reboot   system boot  4.2.0-30-generic Thu Mar  3 11:19 - 13:38 (6+02:18)"
    # "reboot" is not a real user, it shouldn't be listed
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 03, 03, 11, 19, tzinfo=dateutil.tz.tzlocal()))


def test_get_users_at_gone_no_logout(check_output):
    """
    Treat "gone - no logout" as "still logged in".

    That's the only place I've seen it.
    """
    now = datetime.datetime(2016, 04, 07, 12, 8, tzinfo=dateutil.tz.tzlocal())
    lastline = "johan    pts/3        :0               Mon Apr  4 23:10    gone - no logout"

    # Before
    assert not get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 04, 23, 9, tzinfo=dateutil.tz.tzlocal()))

    # During
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime(2016, 04, 04, 23, 10, tzinfo=dateutil.tz.tzlocal()))
    assert set(["johan"]) == get_users_at(
        lastline, now,
        datetime.datetime.now(dateutil.tz.tzlocal()))


def test_get_users_at_just_run_it(check_output):
    # Just tyre kick it live wherever we happen to be. This shouldn't crash.
    px_loginhistory.get_users_at(datetime.datetime.now(dateutil.tz.tzlocal()))


def test_to_timestamp(check_output):
    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    expected = datetime.datetime(2016, 03, 05, 11, 19, tzinfo=dateutil.tz.tzlocal())
    assert px_loginhistory._to_timestamp("Thu Mar  5 11:19", now) == expected

    now = datetime.datetime(2016, 04, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    expected = datetime.datetime(2016, 02, 29, 13, 19, tzinfo=dateutil.tz.tzlocal())
    assert px_loginhistory._to_timestamp("Mon Feb 29 13:19", now) == expected

    now = datetime.datetime(2017, 01, 03, 12, 8, tzinfo=dateutil.tz.tzlocal())
    expected = datetime.datetime(2016, 02, 29, 13, 19, tzinfo=dateutil.tz.tzlocal())
    assert px_loginhistory._to_timestamp("Mon Feb 29 13:19", now) == expected


def test_to_timedelta(check_output):
    assert px_loginhistory._to_timedelta("01:29") == datetime.timedelta(0, hours=1, minutes=29)
    assert px_loginhistory._to_timedelta("4+01:29") == datetime.timedelta(4, hours=1, minutes=29)
    assert px_loginhistory._to_timedelta("34+01:29") == datetime.timedelta(34, hours=1, minutes=29)
