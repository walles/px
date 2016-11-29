import sys
import datetime
import subprocess

import os
import re
import dateutil.tz


# last regexp parts
LAST_USERNAME = "([^ ]+)"
LAST_DEVICE = "([^ ]+)"
LAST_ADDRESS = "([^ ]+)?"
LAST_FROM = "(... ... .. ..:..)"
LAST_DASH = " [- ] "
LAST_TO = "[^(]*"
LAST_DURATION = "([0-9+:]+)"

LAST_RE = re.compile(
  LAST_USERNAME +
  " +" +
  LAST_DEVICE +
  " +" +
  LAST_ADDRESS +
  " +" +
  LAST_FROM +
  LAST_DASH +
  LAST_TO +
  " *(\(" +
  LAST_DURATION +
  "\))?"
)

TIMEDELTA_RE = re.compile("(([0-9]+)\+)?([0-9][0-9]):([0-9][0-9])")

# Month names in English locale
MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


def get_users_at(timestamp, last_output=None, now=None):
    """
    Return a set of strings corresponding to which users were logged in from
    which addresses at a given timestamp.

    Optional argument last_output is the output of "last". Will be filled in by
    actually executing "last" if not provided.

    Optional argument now is the current timestamp for parsing last_output. Will
    be taken from the system clock if not provided.
    """

    if now is None:
        now = datetime.datetime.now(dateutil.tz.tzlocal())

    if last_output is None:
        last_output = call_last()

    users = set()
    for line in last_output.splitlines():
        if not line:
            continue
        if line.startswith("wtmp begins"):
            # This is trailing noise printed by last
            continue
        if line.startswith("reboot "):
            continue
        if line.startswith("shutdown "):
            continue

        match = LAST_RE.match(line)
        if not match:
            sys.stderr.write(
                "WARNING: Please report unmatched last line at {}: <{}>\n".format(
                    "https://github.com/walles/px/issues/new", line))
            continue

        username = match.group(1)
        address = match.group(3)
        from_s = match.group(4)
        duration_s = match.group(6)

        if address:
            username += " from " + address

        try:
            from_timestamp = _to_timestamp(from_s, now)
            if timestamp < from_timestamp:
                continue
        except Exception:
            sys.stderr.write(
                "WARNING: Please report problematic1 last line at {}: <{}>\n".format(
                    "https://github.com/walles/px/issues/new", line))
            continue

        if duration_s is None:
            # Still logged in
            users.add(username)
            continue

        try:
            duration_delta = _to_timedelta(duration_s)
            to_timestamp = from_timestamp + duration_delta
            if timestamp > to_timestamp:
                continue
        except Exception:
            sys.stderr.write(
                "WARNING: Please report problematic2 last line at {}: <{}>\n".format(
                    "https://github.com/walles/px/issues/new", line))
            continue

        users.add(username)

    return users


def call_last():
    """
    Call last and return the result as one big string
    """
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]

    last = subprocess.Popen("last",
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    return last.communicate()[0].decode('utf-8')


def _to_timestamp(string, now):
    """
    Parse a timestamp like "Mon Feb  7 13:19".

    Names of months and days must be in English, make sure you call "last"
    without the LANG= environment variable set.

    Now is the current timestamp, and the returned timestamp is supposed to be
    before now.
    """

    # FIXME: Use day of week as a checksum before returning from this function?

    split = string.split()
    month = MONTHS[split[1]]
    day = int(split[2])

    hour, minute = split[3].split(":")
    hour = int(hour)
    minute = int(minute)

    try:
        timestamp = datetime.datetime(
            now.year, month, day, hour, minute, tzinfo=dateutil.tz.tzlocal())
        if timestamp <= now:
            return timestamp
    except ValueError:
        if month == 2 and day == 29:
            # This happens at leap years when we get the year wrong
            pass
        else:
            raise

    return datetime.datetime(
        now.year - 1, month, day, hour, minute, tzinfo=dateutil.tz.tzlocal())


def _to_timedelta(string):
    match = TIMEDELTA_RE.match(string)

    days = match.group(2)
    if days is None:
        days = 0
    else:
        days = int(days)

    hours = int(match.group(3))

    minutes = int(match.group(4))

    return datetime.timedelta(days, hours=hours, minutes=minutes)
