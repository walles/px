import sys

import re

USERNAME_PART = "([^ ]+)"
DEVICE_PART = "([^ ]+)"
ADDRESS_PART = "([^ ]+)?"
FROM_PART = "(.*)"
DASH_PART = " . "
TO_PART = "(.*)"
DURATION_PART = "([0-9+:]+)"
LAST_RE = re.compile(
  USERNAME_PART +
  " +" +
  DEVICE_PART +
  " +" +
  ADDRESS_PART +
  " +" +
  FROM_PART +
  DASH_PART +
  TO_PART +
  " *\(" +
  DURATION_PART +
  "\)"
)


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

        # username = match.group(1)
        # device = match.group(2)
        # address = match.group(3)
        # from_s = match.group(4)
        # to_s = match.group(5)
        # duration_s = match.group(6)

    return users
