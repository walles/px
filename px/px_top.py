import sys
import tty
import copy
import errno
import signal
import select
import termios
import operator

import os
import px.px_load
import px.px_process
import px.px_terminal


# Used for informing our getch() function that a window resize has occured
SIGWINCH_PIPE = os.pipe()


def adjust_cpu_times(current, baseline):
    """
    Identify processes in current that are also in baseline.

    For all matches, substract the baseline process' CPU time usage from the
    current process' one.

    This way we get CPU times computed from when "px --top" was started, rather
    than from when each process was started.

    Neither current nor baseline are changed by this function.
    """
    pid2proc = {}
    for proc in current:
        pid2proc[proc.pid] = proc

    for baseline_proc in baseline:
        current_proc = pid2proc.get(baseline_proc.pid)
        if current_proc is None:
            # This process is newer than the baseline
            continue

        if current_proc.start_time != baseline_proc.start_time:
            # This PID has been reused
            continue

        if current_proc.cpu_time_seconds is None:
            # We can't substract from None
            continue

        if baseline_proc.cpu_time_seconds is None:
            # We can't substract None
            continue

        current_proc = copy.copy(current_proc)
        current_proc.set_cpu_time_seconds(
            current_proc.cpu_time_seconds - baseline_proc.cpu_time_seconds)
        pid2proc[current_proc.pid] = current_proc

    return pid2proc.values()


def read_select(fds, timeout_seconds):
    """Select on any of the fds becoming ready for read, retry on EINTR"""
    while True:
        try:
            return select.select(fds, [], [], timeout_seconds)[0]
        except select.error as ex:
            if ex[0] == errno.EINTR:
                # EINTR happens when the terminal window is resized by the user,
                # just try again.
                continue

            # Non-EINTR exceptions are unexpected, help!
            raise


def getch(timeout_seconds=0):
    """
    Wait at most timeout_seconds for a character to become available on stdin.

    Returns the character, or None on timeout.
    """
    can_read_from = (
        read_select([sys.stdin.fileno(), SIGWINCH_PIPE[0]], timeout_seconds))

    if len(can_read_from) > 0:
        # Read one byte from the first ready-for-read stream. If more than one
        # stream is ready, we'll catch the second one on the next call to this
        # function, so just doing the first is fine.
        return os.read(can_read_from[0], 1)

    return None


def redraw(baseline, rows, columns):
    """
    Refresh display relative to the given baseline.

    The new display will be (at most) rows rows x columns columns.
    """
    lines = ["System load: " + px_load.get_load_string(), ""]

    adjusted = adjust_cpu_times(px_process.get_all(), baseline)

    # Sort by CPU time used, then most interesting first
    ordered = px_process.order_best_first(adjusted)
    ordered = sorted(ordered, key=operator.attrgetter('cpu_time_seconds'), reverse=True)
    lines += px_terminal.to_screen_lines(ordered, columns)

    # Clear the screen and move cursor to top left corner:
    # https://en.wikipedia.org/wiki/ANSI_escape_code
    #
    # Note that some experimentation was involved in coming up with this
    # exact sequence; if you do first "clear the full screen" then "home"
    # for example, the contents of the previous screen gets added to the
    # scrollback buffer, which isn't what we want. Tread carefully if you
    # intend to change these.
    #
    # Writing to stderr since stderr is rumored not to be buffered.
    CSI = "\x1b["
    sys.stderr.write(CSI + "1J")
    sys.stderr.write(CSI + "H")

    # We need both \r and \n when the TTY is in tty.setraw() mode
    sys.stdout.write("\r\n".join(lines[0:rows]))
    sys.stdout.flush()


def _top():
    baseline = px_process.get_all()
    while True:
        window_size = px_terminal.get_window_size()
        if window_size is None:
            sys.stderr.write("Cannot find terminal window size, are you on a terminal?\r\n")
            exit(1)
        rows, columns = window_size
        redraw(baseline, rows, columns)

        char = getch(timeout_seconds=1)

        # Handle all keypresses before refreshing the display
        while char is not None:
            if char == 'q':
                # The idea here is that if you terminate with "q" you still
                # probably want the heading line on screen. So just do another
                # update with somewhat fewer lines, and you'll get just that.
                rows, columns = px_terminal.get_window_size()
                redraw(baseline, rows - 4, columns)
                return

            char = getch(timeout_seconds=0)


def sigwinch_handler(signum, frame):
    """Handle window resize signals by telling our getch() function to return"""
    # "r" for "refresh" perhaps? The actual letter doesn't matter, as long as it
    # doesn't collide with anything with some meaning other than "please
    # redraw".
    os.write(SIGWINCH_PIPE[1], 'r')


def top():
    if not sys.stdout.isatty():
        sys.stderr.write('Top mode only works on TTYs, try running just "px" instead.\n')
        exit(1)

    signal.signal(signal.SIGWINCH, sigwinch_handler)

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)
    try:
        _top()
    finally:
        tty.setcbreak(fd)

        # tty.setraw() disables local echo, so we have to re-enable it here.
        # See the "source code" comment to this answer:
        # http://stackoverflow.com/a/8758047/473672
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

        # Make sure we actually end up on a new line
        print("")
