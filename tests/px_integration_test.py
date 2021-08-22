import os
import sys

from px import px


def test_run_on_pid(capfd):
    """
    Just run px on a PID.

    The only verification done here is that it doesn't crash,
    there is room for improvement...
    """
    argv = [
        sys.argv[0],
        "--no-pager",  # Paging causes problems on Travis CI
        # Note that px hides our own PID by design, so we look for our
        # parent PID in this test.
        str(os.getppid()),
    ]

    # Enable manual inspection of the output:
    # https://docs.pytest.org/en/latest/capture.html
    with capfd.disabled():
        px._main(argv)
