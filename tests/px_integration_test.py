import os
import sys

from px import px


def test_run_on_pid():
    """
    Just run px on a PID.

    The only verification done here is that it doesn't crash,
    there is room for improvement...
    """
    argv = [
        sys.argv[0],

        # Note that px hides our own PID by design, so we look for our
        # parent PID in this test.
        str(os.getppid())
    ]
    px._main(argv)
