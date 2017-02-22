import sys
import tty
import copy
import errno
import signal
import select
import termios

import os
from . import px_load
from . import px_process
from . import px_terminal
from . import px_load_bar
from . import px_cpuinfo


# Used for informing our getch() function that a window resize has occured
SIGWINCH_PIPE = os.pipe()

# We'll report window resize as this key having been pressed
SIGWINCH_KEY = u'r'

CMD_UNKNOWN = -1
CMD_QUIT = 1
CMD_RESIZE = 2


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


def getch(timeout_seconds=0, fd=None):
    """
    Wait at most timeout_seconds for a character to become available on stdin.

    Returns the character, or None on timeout.
    """
    if fd is None:
        fd = sys.stdin.fileno()

    can_read_from = (
        read_select([fd, SIGWINCH_PIPE[0]], timeout_seconds))

    # Read one byte from the first ready-for-read stream. If more than one
    # stream is ready, we'll catch the second one on the next call to this
    # function, so just doing the first is fine.
    for stream in can_read_from:
        return_me = os.read(stream, 1).decode("UTF-8")
        if len(return_me) > 0:
            return return_me

        # A zero length response means we get EOF from one of the streams. This
        # happens (at least) during testing.
        continue

    return None


def get_notnone_cpu_time_seconds(proc):
    seconds = proc.cpu_time_seconds
    if seconds is not None:
        return seconds
    return 0


def get_toplist(baseline):
    toplist = adjust_cpu_times(px_process.get_all(), baseline)

    # Sort by CPU time used, then most interesting first
    toplist = px_process.order_best_first(toplist)
    toplist = sorted(toplist, key=get_notnone_cpu_time_seconds, reverse=True)

    return toplist


def writebytes(bytestring):
    if sys.version_info.major == 2:
        sys.stdout.write(bytestring)
    else:
        # http://stackoverflow.com/a/908440/473672
        sys.stdout.buffer.write(bytestring)


def clear_screen():
    """
    Clear the screen and move cursor to top left corner:
    https://en.wikipedia.org/wiki/ANSI_escape_code

    Note that some experimentation was involved in coming up with this
    exact sequence; if you do first "clear the full screen" then "home"
    for example, the contents of the previous screen gets added to the
    scrollback buffer, which isn't what we want. Tread carefully if you
    intend to change these.
    """

    CSI = b"\x1b["
    writebytes(CSI + b"1J")
    writebytes(CSI + b"H")


def get_screen_lines(load_bar, baseline, rows, columns):
    load = px_load.get_load_values()
    loadstring = px_load.get_load_string(load)
    loadbar = load_bar.get_bar(load=load[0], columns=40, text=loadstring)
    lines = [
        b"System load: " + loadbar,
        b""]

    toplist_table_lines = px_terminal.to_screen_lines(get_toplist(baseline), columns)
    if toplist_table_lines:
        heading_line = toplist_table_lines[0]
        heading_line = px_terminal.get_string_of_length(heading_line, columns)
        heading_line = px_terminal.inverse_video(heading_line)
        toplist_table_lines[0] = heading_line

    toplist_table_lines = map(lambda s: s.encode('utf-8'), toplist_table_lines)
    lines += toplist_table_lines

    return lines[0:rows]


def redraw(load_bar, baseline, rows, columns, clear=True):
    """
    Refresh display relative to the given baseline.

    The new display will be (at most) rows rows x columns columns.
    """
    lines = get_screen_lines(load_bar, baseline, rows, columns)
    if clear:
        clear_screen()

    # We need both \r and \n when the TTY is in tty.setraw() mode
    writebytes(b"\r\n".join(lines))
    sys.stdout.flush()


def get_command(**kwargs):
    """
    Call getch() and interpret the results.
    """
    char = getch(**kwargs)
    if char is None:
        return None
    assert len(char) > 0

    if char == u'q':
        return CMD_QUIT
    if char == SIGWINCH_KEY:
        return CMD_RESIZE
    return CMD_UNKNOWN


def _top():
    physical, logical = px_cpuinfo.get_core_count()
    load_bar = px_load_bar.PxLoadBar(physical, logical)
    baseline = px_process.get_all()
    while True:
        window_size = px_terminal.get_window_size()
        if window_size is None:
            sys.stderr.write("Cannot find terminal window size, are you on a terminal?\r\n")
            exit(1)
        rows, columns = window_size
        redraw(load_bar, baseline, rows, columns)

        command = get_command(timeout_seconds=1)

        # Handle all keypresses before refreshing the display
        while command is not None:
            if command == CMD_QUIT:
                # The idea here is that if you terminate with "q" you still
                # probably want the heading line on screen. So just do another
                # update with somewhat fewer lines, and you'll get just that.
                rows, columns = px_terminal.get_window_size()
                redraw(load_bar, baseline, rows - 4, columns)
                return

            command = get_command(timeout_seconds=0)


def sigwinch_handler(signum, frame):
    """Handle window resize signals by telling our getch() function to return"""
    # "r" for "refresh" perhaps? The actual letter doesn't matter, as long as it
    # doesn't collide with anything with some meaning other than "please
    # redraw".
    os.write(SIGWINCH_PIPE[1], SIGWINCH_KEY.encode("iso-8859-1"))


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
