import datetime

import pytest

from px import px_loginhistory

from typing import Set

TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo


@pytest.fixture
def check_output(capfd):
    yield None

    out, err = capfd.readouterr()
    assert not err
    assert not out


def get_users_at(
    last_output: str, now: datetime.datetime, testtime: datetime.datetime
) -> Set[str]:
    """
    Ask px_loginhistory to parse last_output given the current timestamp of now.

    Then return the users px_loginhistory claims were logged in at testtime.
    """
    return px_loginhistory.get_users_at(testtime, last_output=last_output, now=now)


def test_get_users_at_range(check_output):
    # Test user logged in between two timestamps
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = "johan     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)"

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 14, 38, tzinfo=TIMEZONE),
    )

    # During
    assert {"johan"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 14, 39, tzinfo=TIMEZONE),
    )
    assert {"johan"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 17, 46, tzinfo=TIMEZONE),
    )
    assert {"johan"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 1, 11, 8, tzinfo=TIMEZONE),
    )

    # After
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 1, 11, 9, tzinfo=TIMEZONE),
    )


def test_get_users_at_range_raspbian(check_output):
    # Test user logged in between two timestamps, test string is from a Raspbian
    # system: https://github.com/walles/px/issues/130
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = (
        "sk-tv                                  Thu Mar 31 14:39 - down   (20:29)"
    )

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 14, 38, tzinfo=TIMEZONE),
    )

    # During
    assert {"sk-tv"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 14, 39, tzinfo=TIMEZONE),
    )
    assert {"sk-tv"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 17, 46, tzinfo=TIMEZONE),
    )
    assert {"sk-tv"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 1, 11, 8, tzinfo=TIMEZONE),
    )

    # After
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 1, 11, 9, tzinfo=TIMEZONE),
    )


def test_get_users_at_still_logged_in(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = "johan     ttys000                   Sun Apr  3 11:54   still logged in"

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 3, 11, 53, tzinfo=TIMEZONE),
    )

    # During
    assert {"johan"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 3, 11, 54, tzinfo=TIMEZONE),
    )
    assert {"johan"} == get_users_at(lastline, now, datetime.datetime.now(TIMEZONE))


def test_get_users_at_remote(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = (
        "root     pts/1        10.1.6.120       Tue Jan 28 05:59   still logged in"
    )

    assert {"root from 10.1.6.120"} == get_users_at(
        lastline, now, datetime.datetime.now(TIMEZONE)
    )


def test_get_users_at_local_osx(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = "johan     ttys000                   Sun Apr  3 11:54   still logged in"

    assert {"johan"} == get_users_at(lastline, now, datetime.datetime.now(TIMEZONE))


def test_get_users_at_local_linux(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = (
        "johan    pts/2        :0               Wed Mar  9 13:25 - 13:38  (00:12)"
    )

    assert {"johan from :0"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 9, 13, 26, tzinfo=TIMEZONE),
    )


def test_get_users_at_until_crash(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = "johan     ttys001                   Thu Nov 26 19:55 - crash (27+07:11)"

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2015, 11, 26, 19, 54, tzinfo=TIMEZONE),
    )

    # During
    assert {"johan"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2015, 11, 26, 19, 55, tzinfo=TIMEZONE),
    )
    assert {"johan"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2015, 12, 10, 19, 53, tzinfo=TIMEZONE),
    )

    # A bit after
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2015, 12, 26, 19, 55, tzinfo=TIMEZONE),
    )


def test_get_users_at_until_shutdown_osx(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = (
        "_mbsetupuser  console                   Mon Jan 18 20:31 - shutdown (34+01:29)"
    )

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 1, 18, 20, 30, tzinfo=TIMEZONE),
    )

    # During
    assert {"_mbsetupuser"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 1, 18, 20, 31, tzinfo=TIMEZONE),
    )
    assert {"_mbsetupuser"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 2, 18, 20, 30, tzinfo=TIMEZONE),
    )

    # A bit after
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 2, 28, 20, 30, tzinfo=TIMEZONE),
    )


def test_get_users_at_until_shutdown_linux(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = (
        "johan    :0           :0               Sat Mar 26 22:04 - down   (00:08)"
    )

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 26, 22, 3, tzinfo=TIMEZONE),
    )

    # During
    assert {"johan from :0"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 26, 22, 4, tzinfo=TIMEZONE),
    )
    assert {"johan from :0"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 26, 22, 9, tzinfo=TIMEZONE),
    )

    # A bit after
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 26, 22, 15, tzinfo=TIMEZONE),
    )


def test_get_users_at_multiple(check_output):
    # Test multiple users logged in between two timestamps
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    lastline = "\n".join(
        [
            "johan1     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
            "johan2     ttys000                   Thu Mar 31 14:39 - 11:08  (20:29)",
        ]
    )

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 14, 38, tzinfo=TIMEZONE),
    )

    # During
    assert {"johan1", "johan2"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 14, 39, tzinfo=TIMEZONE),
    )
    assert {"johan1", "johan2"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 31, 17, 46, tzinfo=TIMEZONE),
    )
    assert {"johan1", "johan2"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 1, 11, 8, tzinfo=TIMEZONE),
    )

    # After
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 1, 11, 9, tzinfo=TIMEZONE),
    )


def test_get_users_at_pseudousers_osx(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)

    # Note trailing space in test string, we get that from last on OS X 10.11.3
    lastline = "reboot    ~                         Fri Oct 23 06:50 "
    # "reboot" is not a real user, it shouldn't be listed
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2015, 10, 23, 6, 50, tzinfo=TIMEZONE),
    )

    # Note trailing space in test string, we get that from last on OS X 10.11.3
    lastline = "shutdown  ~                         Fri Oct 23 06:49 "
    # "shutdown" is not a real user, it shouldn't be listed
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2015, 10, 23, 6, 49, tzinfo=TIMEZONE),
    )


def test_get_users_at_pseudousers_linux(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)

    lastline = (
        "reboot   system boot  4.2.0-30-generic Thu Mar  3 11:19 - 13:38 (6+02:18)"
    )
    # "reboot" is not a real user, it shouldn't be listed
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 3, 3, 11, 19, tzinfo=TIMEZONE),
    )


def test_get_users_at_gone_no_logout(check_output):
    """
    Treat "gone - no logout" as "still logged in".

    That's the only place I've seen it.
    """
    now = datetime.datetime(2016, 4, 7, 12, 8, tzinfo=TIMEZONE)
    lastline = (
        "johan    pts/3        :0               Mon Apr  4 23:10    gone - no logout"
    )

    # Before
    assert not get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 4, 23, 9, tzinfo=TIMEZONE),
    )

    # During
    assert {"johan from :0"} == get_users_at(
        lastline,
        now,
        datetime.datetime(2016, 4, 4, 23, 10, tzinfo=TIMEZONE),
    )
    assert {"johan from :0"} == get_users_at(
        lastline, now, datetime.datetime.now(TIMEZONE)
    )


def test_get_users_at_trailing_noise(check_output):
    now = datetime.datetime(2016, 4, 7, 12, 8, tzinfo=TIMEZONE)
    assert not get_users_at("", now, now)

    # Note trailing space in test string, we get that from last on OS X 10.11.3
    assert not get_users_at("wtmp begins Thu Oct  1 22:54 ", now, now)


def test_get_users_at_unexpected_last_output(caplog):
    UNEXPECTED = "glasskiosk"

    now = datetime.datetime(2016, 4, 7, 12, 8, tzinfo=TIMEZONE)
    assert not get_users_at(UNEXPECTED, now, now)

    assert UNEXPECTED in caplog.text


def test_get_users_at_just_run_it(check_output):
    # Just tyre kick it live wherever we happen to be. This shouldn't crash.
    px_loginhistory.get_users_at(datetime.datetime.now(TIMEZONE))


def test_to_timestamp(check_output):
    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    expected = datetime.datetime(2016, 3, 5, 11, 19, tzinfo=TIMEZONE)
    assert px_loginhistory._to_timestamp("Thu Mar  5 11:19", now) == expected

    now = datetime.datetime(2016, 4, 3, 12, 8, tzinfo=TIMEZONE)
    expected = datetime.datetime(2016, 2, 29, 13, 19, tzinfo=TIMEZONE)
    assert px_loginhistory._to_timestamp("Mon Feb 29 13:19", now) == expected

    now = datetime.datetime(2017, 1, 3, 12, 8, tzinfo=TIMEZONE)
    expected = datetime.datetime(2016, 2, 29, 13, 19, tzinfo=TIMEZONE)
    assert px_loginhistory._to_timestamp("Mon Feb 29 13:19", now) == expected


def test_to_timedelta(check_output):
    assert px_loginhistory._to_timedelta("01:29") == datetime.timedelta(
        0, hours=1, minutes=29
    )
    assert px_loginhistory._to_timedelta("4+01:29") == datetime.timedelta(
        4, hours=1, minutes=29
    )
    assert px_loginhistory._to_timedelta("34+01:29") == datetime.timedelta(
        34, hours=1, minutes=29
    )


def test_realworld_debian(check_output):
    """
    Regression test for https://github.com/walles/px/issues/48
    """
    now = datetime.datetime(2016, 12, 6, 9, 21, tzinfo=TIMEZONE)
    testtime = datetime.datetime(2016, 10, 24, 15, 34, tzinfo=TIMEZONE)
    lastline = (
        "norbert  pts/3        mosh [29846]     Wed Oct 24 15:33 - 15:34  (00:01)"
    )

    assert {"norbert from mosh"} == get_users_at(lastline, now, testtime)
