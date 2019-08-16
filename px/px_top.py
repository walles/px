# coding=utf-8

import sys
import tty
import copy
import time
import errno
import signal
import select
import termios
import unicodedata

import os
from . import px_load
from . import px_process
from . import px_terminal
from . import px_load_bar
from . import px_cpuinfo
from . import px_processinfo
from . import px_launchcounter

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List      # NOQA
    from typing import Dict      # NOQA
    from typing import Union     # NOQA
    from typing import Optional  # NOQA
    from six import text_type    # NOQA

# Used for informing our getch() function that a window resize has occured
SIGWINCH_PIPE = os.pipe()

# We'll report window resize as this key having been pressed.
#
# NOTE: This must be detected as non-printable by handle_search_keypress().
SIGWINCH_KEY = u'\x00'

CMD_WHATEVER = -1
CMD_QUIT = 1
CMD_RESIZE = 2
CMD_HANDLED = 3

KEY_ESC = "\x1b"
KEY_BACKSPACE = "\x1b[3~"
KEY_DELETE = "\x7f"
KEY_UPARROW = "\x1b[A"
KEY_DOWNARROW = "\x1b[B"
KEY_ENTER = "\x0d"

SEARCH_PROMPT = px_terminal.bold("Search (ESC to cancel): ")
SEARCH_CURSOR = px_terminal.inverse_video(" ")

MODE_BASE = 0
MODE_SEARCH = 1

initial_termios_attr = None  # type: Optional[List[Union[int, List[bytes]]]]

top_mode = MODE_BASE  # type: int
search_string = None  # type: Optional[text_type]

# Which pid were we last hovering?
last_highlighted_pid = None  # type: Optional[int]

# Which row were we last hovering? Go for this one if
# we can't use last_pid.
last_highlighted_row = 0  # type: int

# Has the user manually moved the highlight? If not, just stay on the top
# row even if the tow PID moves away.
highlight_has_moved = False  # type: bool

# When we last polled the system for a process list, in seconds since the Epoch
last_process_poll = 0.0


class ConsumableString(object):
    def __init__(self, string):
        # type: (text_type) -> None
        self._string = string

    def __len__(self):
        return len(self._string)

    def consume(self, to_consume):
        # type: (text_type) -> bool
        if not self._string.startswith(to_consume):
            return False

        self._string = self._string[len(to_consume):]
        return True


def adjust_cpu_times(baseline, current):
    # type: (List[px_process.PxProcess], List[px_process.PxProcess]) -> List[px_process.PxProcess]
    """
    Identify processes in current that are also in baseline.

    For all matches, substract the baseline process' CPU time usage from the
    current process' one.

    This way we get CPU times computed from when "px --top" was started, rather
    than from when each process was started.

    Neither current nor baseline are changed by this function.
    """
    pid2proc = {}  # type: Dict[int,px_process.PxProcess]
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

    return list(pid2proc.values())


def read_select(fds, timeout_seconds):
    """Select on any of the fds becoming ready for read, retry on EINTR"""

    # NOTE: If you change this method, you must test running "px --top" and
    # resize the window in both Python 2 and Python 3.
    while True:
        try:
            return select.select(fds, [], [], timeout_seconds)[0]
        except OSError as ose:
            # Python 3
            if ose.errno == errno.EINTR:
                # EINTR happens when the terminal window is resized by the user,
                # just try again.
                continue

            # Non-EINTR exceptions are unexpected, help!
            raise
        except select.error as se:
            # Python 2
            if se.args[0] == errno.EINTR:
                # EINTR happens when the terminal window is resized by the user,
                # just try again.
                continue

            # Non-EINTR exceptions are unexpected, help!
            raise


def getch(timeout_seconds=0, fd=None):
    # type: (int, int) -> Optional[ConsumableString]
    """
    Wait at most timeout_seconds for a character to become available on stdin.

    Returns the character, or None on timeout.
    """
    if fd is None:
        fd = sys.stdin.fileno()

    can_read_from = (
        read_select([fd, SIGWINCH_PIPE[0]], timeout_seconds))

    # Read all(ish) bytes from the first ready-for-read stream. If more than one
    # stream is ready, we'll catch the second one on the next call to this
    # function, so just doing the first is fine.
    for stream in can_read_from:
        string = os.read(stream, 1234).decode("UTF-8")
        if len(string) > 0:
            return ConsumableString(string)

        # A zero length response means we got EOF from one of the streams. This
        # happens (at least) during testing.
        continue

    return None


def get_notnone_cpu_time_seconds(proc):
    seconds = proc.cpu_time_seconds
    if seconds is not None:
        return seconds
    return 0


def get_toplist(baseline, current):
    # type: (List[px_process.PxProcess], List[px_process.PxProcess]) -> List[px_process.PxProcess]
    toplist = adjust_cpu_times(baseline, current)

    # Sort by CPU time used, then most interesting first
    toplist = px_process.order_best_first(toplist)
    toplist = sorted(toplist, key=get_notnone_cpu_time_seconds, reverse=True)

    return toplist


def writebytes(bytestring):
    # type: (bytes) -> None
    os.write(sys.stdout.fileno(), bytestring)


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


def get_line_to_highlight(toplist, max_process_count):
    # type: (List[px_process.PxProcess], int) -> Optional[int]
    global last_highlighted_pid
    global last_highlighted_row
    global highlight_has_moved

    if not toplist:
        # Toplist is empty or None
        return None

    if max_process_count <= 0:
        # No space for the highlight
        return None

    # Before the user has moved the highlight, we don't follow a particular PID
    if last_highlighted_pid is not None and highlight_has_moved:
        # Find PID line in list
        pid_line = None
        for index, process in enumerate(toplist):
            if process.pid == last_highlighted_pid:
                pid_line = index
                break
        if pid_line is not None and pid_line < max_process_count:
            last_highlighted_row = pid_line
            return pid_line

    # No PID or not found, go for the last highlighted line instead...

    # Bound highlight to toplist length and screen height
    last_highlighted_row = min(
        last_highlighted_row, max_process_count - 1, len(toplist) - 1)
    if last_highlighted_row < 0:
        last_highlighted_row = 0

    if last_highlighted_row > 0:
        highlight_has_moved = True

    # Stay on the top line unless the user has explicitly moved the highlight
    last_highlighted_pid = toplist[last_highlighted_row].pid

    return last_highlighted_row


def get_screen_lines(
    load_bar,  # type: px_load_bar.PxLoadBar
    toplist,   # type: List[px_process.PxProcess]
    launchcounter,  # type: px_launchcounter.Launchcounter
    rows,      # type: int
    columns,   # type: int
    include_footer=True,  # type: bool
    search=None,  # type: Optional[text_type]
):
    # type: (...) -> List[text_type]

    if search is not None:
        # Note that we accept partial user name match, otherwise incrementally typing
        # a username becomes weird for the ptop user
        toplist = list(filter(lambda p: p.match(search, require_exact_user=False), toplist))

    # Hand out different amount of lines to the different sections
    header_height = 2
    footer_height = 0
    cputop_minheight = 10
    if include_footer:
        footer_height = 1

    # Print header
    load = px_load.get_load_values()
    loadstring = px_load.get_load_string(load)
    loadbar = load_bar.get_bar(load=load[0], columns=40, text=loadstring)
    lines = [
        u"System load: " + loadbar,
        u""]

    # Create a launchers section
    launches_maxheight = rows - header_height - cputop_minheight - footer_height
    launchlines = []  # type: List[text_type]
    if launches_maxheight >= 3:
        launchlines = launchcounter.get_screen_lines(columns)
        if len(launchlines) > 0:
            # Add a section header
            launchlines = [
                '',
                px_terminal.bold(
                    "Launched binaries, launch counts in (parentheses)")
            ] + launchlines

            # Cut if we got too many lines
            launchlines = launchlines[0:launches_maxheight]

    # Compute cputop height now that we know how many launchlines we have
    cputop_height = rows - header_height - len(launchlines) - footer_height

    # -2 = Section name + column headings
    max_process_count = cputop_height - 2
    if search is not None:
        # Search prompt needs one line
        max_process_count -= 1

    toplist_table_lines = px_terminal.to_screen_lines(toplist, columns)
    if toplist_table_lines:
        heading_line = toplist_table_lines[0]
        heading_line = px_terminal.get_string_of_length(heading_line, columns)
        heading_line = px_terminal.underline_bold(heading_line)

        highlight_me = get_line_to_highlight(toplist, max_process_count)
        if highlight_me is not None:
            # The "+ 1" here is to skip the heading line
            highlighted = toplist_table_lines[highlight_me + 1]
            highlighted = px_terminal.get_string_of_length(highlighted, columns)
            highlighted = px_terminal.inverse_video(highlighted)

            # The "+ 1" here is to skip the heading line
            toplist_table_lines[highlight_me + 1] = highlighted

        toplist_table_lines[0] = heading_line

    # Ensure that we cover the whole screen, even if it's higher than the
    # number of processes
    toplist_table_lines += rows * ['']

    lines += [px_terminal.bold("Top CPU using processes")]
    if search is not None:
        lines += [SEARCH_PROMPT + search + SEARCH_CURSOR]

    lines += toplist_table_lines[0:max_process_count + 1]  # +1 for the column headings

    lines += launchlines

    if include_footer:
        footer_line = u"  q - Quit  / - Search  ↑↓ - Move selection  Enter - Select"
        footer_line = px_terminal.get_string_of_length(footer_line, columns)
        footer_line = px_terminal.inverse_video(footer_line)

        lines += [footer_line]

    return lines


def redraw(
    load_bar,  # type: px_load_bar.PxLoadBar
    toplist,   # type: List[px_process.PxProcess]
    launchcounter,  # type: px_launchcounter.Launchcounter
    rows,      # type: int
    columns,   # type: int
    clear=True,  # type: bool
    include_footer=True  # type: bool
):
    # type: (...) -> None
    """
    Refresh display.

    The new display will be rows rows x columns columns.
    """
    global search_string
    lines = get_screen_lines(
        load_bar, toplist, launchcounter, rows, columns, include_footer,
        search=search_string)
    if clear:
        clear_screen()

    # We need both \r and \n when the TTY is in tty.setraw() mode
    writebytes(u"\r\n".join(lines).encode('utf-8'))
    sys.stdout.flush()


def restore_display():
    fd = sys.stdin.fileno()
    tty.setcbreak(fd)

    # tty.setraw() disables local echo, so we have to re-enable it here.
    # See the "source code" comment to this answer:
    # http://stackoverflow.com/a/8758047/473672
    global initial_termios_attr
    if initial_termios_attr:
        termios.tcsetattr(fd, termios.TCSADRAIN, initial_termios_attr)


# Print info about PID and exit
def print_info_and_quit(pid):
    # type: (Optional[int]) -> None
    if pid is None:
        # Nothing selected, never mind
        return

    # Is this PID available?
    processes = px_process.get_all()
    process = px_processinfo.find_process_by_pid(pid, processes)
    if not process:
        # Process not available, never mind
        return

    restore_display()

    # Visually distance ourselves from the ptop view
    print("")
    print("")

    px_processinfo.print_process_info(process, processes)
    sys.exit(0)


def handle_search_keypresses(key_sequence):
    # type: (ConsumableString) -> None
    global search_string
    global last_highlighted_row
    global last_highlighted_pid

    # If this triggers our top_mode state machine is broken
    assert search_string is not None

    # NOTE: Uncomment to debug input characters
    # search_string = ":".join("{:02x}".format(ord(c)) for c in key_sequence._string)
    # return

    while len(key_sequence) > 0:
        if key_sequence.consume(KEY_BACKSPACE):
            search_string = search_string[:-1]
        elif key_sequence.consume(KEY_DELETE):
            search_string = search_string[:-1]
        elif key_sequence.consume(KEY_UPARROW):
            last_highlighted_row -= 1
            last_highlighted_pid = None
        elif key_sequence.consume(KEY_DOWNARROW):
            last_highlighted_row += 1
            last_highlighted_pid = None
        elif key_sequence.consume(KEY_ENTER):
            print_info_and_quit(last_highlighted_pid)
        elif key_sequence._string == KEY_ESC:
            # Exit search mode
            global top_mode
            top_mode = MODE_BASE
            search_string = None
            return
        else:
            # Unable to consume more, give up
            break

    if len(key_sequence) == 0:
        return

    if KEY_ESC in key_sequence._string:
        # Some special key, unprintable, unhandled, never mind
        return

    try:
        for char in key_sequence._string:
            if unicodedata.category(char).startswith("C"):
                # Non-printable character, see:
                # http://www.unicode.org/reports/tr44/#GC_Values_Table
                return
    except TypeError:
        # Unable to type check this, let's not add it, just to be safe
        return

    search_string += key_sequence._string


def get_command(**kwargs):
    """
    Call getch() and interpret the results.
    """
    input = getch(**kwargs)
    if input is None:
        return None
    assert len(input) > 0

    global top_mode
    if top_mode == MODE_SEARCH:
        handle_search_keypresses(input)
        return CMD_HANDLED

    global last_highlighted_row
    global last_highlighted_pid
    while len(input) > 0:
        if input.consume(KEY_UPARROW):
            last_highlighted_row -= 1
            last_highlighted_pid = None
        elif input.consume(KEY_DOWNARROW):
            last_highlighted_row += 1
            last_highlighted_pid = None
        elif input.consume(KEY_ENTER):
            print_info_and_quit(last_highlighted_pid)
        elif input.consume(u'/'):
            global search_string
            top_mode = MODE_SEARCH
            search_string = ""
            return None
        elif input.consume(u'q'):
            return CMD_QUIT
        elif input.consume(SIGWINCH_KEY):
            return CMD_RESIZE
        else:
            # Unable to consume anything, give up
            break

    return CMD_WHATEVER


def _top():
    physical, logical = px_cpuinfo.get_core_count()
    load_bar = px_load_bar.PxLoadBar(physical, logical)
    baseline = px_process.get_all()
    current = baseline
    launchcounter = px_launchcounter.Launchcounter()
    while True:
        launchcounter.update(current)
        window_size = px_terminal.get_window_size()
        if window_size is None:
            sys.stderr.write("Cannot find terminal window size, are you on a terminal?\r\n")
            exit(1)
        rows, columns = window_size
        toplist = get_toplist(baseline, current)
        redraw(load_bar, toplist, launchcounter, rows, columns)

        command = get_command(timeout_seconds=1)

        # Handle all keypresses before refreshing the display
        while command is not None:
            if command == CMD_QUIT:
                # The idea here is that if you terminate with "q" you still
                # probably want the heading line on screen. So just do another
                # update with somewhat fewer lines, and you'll get just that.
                redraw(load_bar, toplist, launchcounter, rows - 4, columns, include_footer=False)
                return

            command = get_command(timeout_seconds=0)

        # For interactivity reasons, don't do this too often
        global last_process_poll
        now = time.time()
        delta_seconds = now - last_process_poll
        if delta_seconds >= 0.8:
            current = px_process.get_all()
            last_process_poll = now


def sigwinch_handler(signum, frame):
    """Handle window resize signals by telling our getch() function to return"""
    # "r" for "refresh" perhaps? The actual letter doesn't matter, as long as it
    # doesn't collide with anything with some meaning other than "please
    # redraw".
    os.write(SIGWINCH_PIPE[1], SIGWINCH_KEY.encode("utf-8"))


def top():
    if not sys.stdout.isatty():
        sys.stderr.write('Top mode only works on TTYs, try running just "px" instead.\n')
        exit(1)

    signal.signal(signal.SIGWINCH, sigwinch_handler)

    fd = sys.stdin.fileno()

    global initial_termios_attr
    initial_termios_attr = termios.tcgetattr(sys.stdin.fileno())

    tty.setraw(fd)

    try:
        _top()
    finally:
        restore_display()

        # Make sure we actually end up on a new line
        print("")
