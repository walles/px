import datetime
import sys

import re


# last regexp parts
LAST_USERNAME = "([^ ]+)"
LAST_DEVICE = "([^ ]+)"
LAST_ADDRESS = "([^ ]+)?"
LAST_FROM = "(... ... .. ..:..)"
LAST_DASH = " . "
LAST_TO = "(..:..)"
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
  " *\(" +
  LAST_DURATION +
  "\)"
)

TIMEDELTA_RE = re.compile("(([0-9]+)\+)?([0-9][0-9]):([0-9][0-9])")


def get_users_at(timestamp, last_output=None, now=None):
    """
    Return a set of strings corresponding to which users were logged in from
    which addresses at a given timestamp.

    Optional argument last_output is the output of "last". Will be filled in by
    actually executing "last" if not provided.

    Optional argument now is the current timestamp for parsing last_output. Will
    be taken from the system clock if not provided.
    """
    users = set()
    for line in last_output.splitlines():
        match = LAST_RE.match(line)
        if not match:
            sys.stderr.write(
                "WARNING: Please report unmatched last line at {}: <{}>\n".format(
                    "https://github.com/walles/px/issues/new", line))
            continue

        username = match.group(1)
        device = match.group(2)
        address = match.group(3)
        from_s = match.group(4)
        to_s = match.group(5)
        duration_s = match.group(6)
        print("FIXME: Remove this printout: u={}, d={}, a={}, f={}, t={}, d={}".format(
            username, device, address, from_s, to_s, duration_s
        ))

        try:
            from_timestamp = _to_timestamp(from_s, now)
            if timestamp < from_timestamp:
                continue
        except Exception:
            sys.stderr.write(
                "WARNING: Please report problematic1 last line at {}: <{}>\n".format(
                    "https://github.com/walles/px/issues/new", line))
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


def _to_timestamp(string, now):
    return None


def _to_timedelta(string):
    match = TIMEDELTA_RE.match(string)

    days = match.group(2)
    if days is None:
        days = 0
    else:
        days = int(days)

    hours = int(match.group(3))

    minutes = int(match.group(4))

    return datetime.timedelta(days, hours, minutes)
