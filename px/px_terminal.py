import sys

import os


def get_window_size():
    """
    Return the terminal window size as tuple (rows, columns) if available, or
    None if not.
    """

    if not sys.stdout.isatty():
        # We shouldn't truncate lines when piping
        return None

    result = os.popen('stty size', 'r').read().split()
    if len(result) < 2:
        # Getting the terminal window width failed, don't truncate
        return None

    rows, columns = result
    columns = int(columns)
    if columns < 1:
        # This seems to happen during OS X CI runs:
        # https://travis-ci.org/walles/px/jobs/113134994
        return None

    rows = int(rows)
    if rows < 1:
        # Don't know if this actually happens, we just do it for symmetry with
        # the columns check above
        return None

    return (rows, columns)
