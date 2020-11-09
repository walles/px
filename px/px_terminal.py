import os
import sys
import errno
import signal
import select
import termios
import tty

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type    # NOQA
    from typing import List      # NOQA
    from typing import Tuple     # NOQA
    from typing import Union     # NOQA
    from typing import Optional  # NOQA
    from typing import Iterable  # NOQA
    from . import px_process     # NOQA


KEY_ESC = "\x1b"
KEY_BACKSPACE = "\x1b[3~"
KEY_DELETE = "\x7f"
KEY_UPARROW = "\x1b[A"
KEY_DOWNARROW = "\x1b[B"
KEY_ENTER = "\x0d"


initial_termios_attr = None  # type: Optional[List[Union[int, List[bytes]]]]


CSI = "\x1b["

"""
Clear the screen and move cursor to top left corner:
https://en.wikipedia.org/wiki/ANSI_escape_code

Note that some experimentation was involved in coming up with this
exact sequence; if you do first "clear the full screen" then "home"
for example, the contents of the previous screen gets added to the
scrollback buffer, which isn't what we want. Tread carefully if you
intend to change these.
"""
CLEAR_SCREEN = CSI + u"1J" + CSI + u"H"

# Actually this is "Move 998 down and 999 right", but as long as people's
# terminal windows are smaller than that it will work fine.
#
# Inspired by: https://stackoverflow.com/a/53168713/473672
CURSOR_TO_BOTTOM_RIGHT = CSI + u"998B" + CSI + u"999C"


# Used for informing our getch() function that a window resize has occured
SIGWINCH_PIPE = os.pipe()

# We'll report window resize as this key having been pressed.
#
# NOTE: This must be detected as non-printable by handle_search_keypress().
SIGWINCH_KEY = u'\x00'

_enable_color = True

def disable_color():
    global _enable_color
    _enable_color = False

def sigwinch_handler(signum, frame):
    """Handle window resize signals by telling our getch() function to return"""
    # "r" for "refresh" perhaps? The actual letter doesn't matter, as long as it
    # doesn't collide with anything with some meaning other than "please
    # redraw".
    os.write(
        SIGWINCH_PIPE[1],
        SIGWINCH_KEY.encode("utf-8"))

# Subscribe to window size change signals
signal.signal(signal.SIGWINCH, sigwinch_handler)


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


def read_select(
    fds,  # type: List[int]
    timeout_seconds=None  # type: Optional[int]
):
    # type: (...) -> List[int]
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


def getch(timeout_seconds=None, fd=None):
    # type: (Optional[int], int) -> Optional[ConsumableString]
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


class TerminalError(Exception):
    def __init__(self, message):
        super(TerminalError, self).__init__(message)


def get_window_size():
    # type: () -> Tuple[int, int]
    """
    Return the terminal window size as tuple (rows, columns).

    Raises a TerminalError if the window size is unavailable.
    """
    if not sys.stdout.isatty():
        # We shouldn't truncate lines when piping
        raise TerminalError("Not a TTY, window size not available")

    result = None
    with os.popen('stty size', 'r') as stty_size:
        result = stty_size.read().split()
    if len(result) < 2:
        # Getting the terminal window width failed, don't truncate
        raise TerminalError("Incomplete response to window size query")

    columns = int(result[1])
    if columns < 1:
        # This seems to happen during OS X CI runs:
        # https://travis-ci.org/walles/px/jobs/113134994
        raise TerminalError("Window width unreasonably small: " + str(columns))

    rows = int(result[0])
    if rows < 1:
        # Don't know if this actually happens, we just do it for symmetry with
        # the columns check above
        raise TerminalError("Window height unreasonably small: " + str(rows))

    return (rows, columns)


def draw_screen_lines(lines, clear=True):
    # type: (List[text_type], bool) -> None

    # We need both \r and \n when the TTY is in tty.setraw() mode
    linestring = u"\r\n".join(lines)

    if clear:
        screen_bytes = CLEAR_SCREEN + linestring
    else:
        screen_bytes = linestring

    screen_bytes += CURSOR_TO_BOTTOM_RIGHT

    os.write(sys.stdout.fileno(), screen_bytes.encode('utf-8'))


def to_screen_lines(procs,  # type: List[px_process.PxProcess]
                    columns,  # type: Optional[int]
                    row_to_highlight,  # type: Optional[int]
                    highlight_heading  # type: Optional[text_type]
                    ):
    # type: (...) -> List[text_type]
    """
    Returns an array of lines that can be printed to screen. Each line is at
    most columns wide.

    If columns is None, line lengths are unbounded.

    If highligh_heading contains a column name, that column will be highlighted.
    The column name must be from the hard coded list in this function, see below.
    """

    headings = [u"PID", u"COMMAND", u"USERNAME", u"CPU", u"CPUTIME", u"RAM", u"COMMANDLINE"]
    highlight_column = None  # type: Optional[int]
    if highlight_heading is not None:
        highlight_column = headings.index(highlight_heading)

    # Compute widest width for pid, command, user, cpu and memory usage columns
    pid_width = len(headings[0])
    command_width = len(headings[1])
    username_width = len(headings[2])
    cpu_width = len(headings[3])
    cputime_width = len(headings[4])
    mem_width = len(headings[5])
    for proc in procs:
        pid_width = max(pid_width, len(str(proc.pid)))
        command_width = max(command_width, len(proc.command))
        username_width = max(username_width, len(proc.username))
        cpu_width = max(cpu_width, len(proc.cpu_percent_s))
        cputime_width = max(cputime_width, len(proc.cpu_time_s))
        mem_width = max(mem_width, len(proc.memory_percent_s))

    format = (
        u'{:>' + str(pid_width) +
        u'} {:' + str(command_width) +
        u'} {:' + str(username_width) +
        u'} {:>' + str(cpu_width) +
        u'} {:>' + str(cputime_width) +
        u'} {:>' + str(mem_width) + u'} {}')

    # Print process list using the computed column widths
    lines = []

    heading_line = format.format(
        headings[0], headings[1], headings[2], headings[3], headings[4], headings[5], headings[6])
    heading_line_length = len(heading_line)
    heading_line_delta = 0
    if columns is not None:
        heading_line_delta = columns - heading_line_length

    # Highlight the highlight_column
    if highlight_column is not None:
        headings[highlight_column] = underline(headings[highlight_column])
    heading_line = format.format(
        headings[0], headings[1], headings[2], headings[3], headings[4], headings[5], headings[6])

    # Set heading line length
    if heading_line_delta > 0:
        heading_line += heading_line_delta * u' '
    if heading_line_delta < 0:
        new_length = heading_line_length + heading_line_delta
        heading_line = crop_ansi_string_at_length(heading_line, new_length)

    heading_line = bold(heading_line)
    lines.append(heading_line)

    max_cpu_percent_s = None  # type: Optional[text_type]
    max_cpu_percent = 0.0
    max_memory_percent_s = None  # type: Optional[text_type]
    max_memory_percent = 0.0
    max_cpu_time_s = None  # type: Optional[text_type]
    max_cpu_time = 0.0
    for proc in procs:
        if proc.cpu_percent is not None and proc.cpu_percent > max_cpu_percent:
            max_cpu_percent = proc.cpu_percent
            max_cpu_percent_s = proc.cpu_percent_s
        if proc.memory_percent is not None and proc.memory_percent > max_memory_percent:
            max_memory_percent = proc.memory_percent
            max_memory_percent_s = proc.memory_percent_s
        if proc.cpu_time_seconds is not None and proc.cpu_time_seconds > max_cpu_time:
            max_cpu_time = proc.cpu_time_seconds
            max_cpu_time_s = proc.cpu_time_s

    for line_number, proc in enumerate(procs):
        cpu_percent_s = proc.cpu_percent_s
        if proc.cpu_percent_s == "0%":
            cpu_percent_s = faint(cpu_percent_s.rjust(cpu_width))
        elif proc.cpu_percent_s == max_cpu_percent_s:
            cpu_percent_s = bold(cpu_percent_s.rjust(cpu_width))

        memory_percent_s = proc.memory_percent_s
        if proc.memory_percent_s == "0%":
            memory_percent_s = faint(memory_percent_s.rjust(mem_width))
        elif proc.memory_percent_s == max_memory_percent_s:
            memory_percent_s = bold(memory_percent_s.rjust(mem_width))

        cpu_time_s = proc.cpu_time_s
        if proc.cpu_time_s == max_cpu_time_s:
            cpu_time_s = bold(cpu_time_s.rjust(cputime_width))

        line = format.format(
            proc.pid, proc.command, proc.username,
            cpu_percent_s, cpu_time_s,
            memory_percent_s, proc.cmdline)

        cropped = line
        if row_to_highlight == line_number:
            cropped = get_string_of_length(cropped, columns)
            cropped = inverse_video(cropped)
        elif columns is not None:
            cropped = crop_ansi_string_at_length(line, columns)
        lines.append(cropped)

    lines[0] = heading_line

    return lines


def inverse_video(string):
    # type: (text_type) -> text_type
    global _enable_color
    if not _enable_color:
        return string
    return CSI + "7m" + string + CSI + "27m"


def bold(string):
    # type: (text_type) -> text_type
    global _enable_color
    if not _enable_color:
        return string
    return CSI + "1m" + string + CSI + "22m"


def faint(string):
    # type: (text_type) -> text_type
    global _enable_color
    if not _enable_color:
        return string
    return CSI + "2m" + string + CSI + "22m"


def underline(string):
    # type: (text_type) -> text_type
    global _enable_color
    if not _enable_color:
        return string
    return CSI + "4m" + string + CSI + "24m"


def red(string):
    # type: (text_type) -> text_type
    global _enable_color
    if not _enable_color:
        return string
    return CSI + "1;30;41m" + string + CSI + "49;39;22m"


def yellow(string):
    # type: (text_type) -> text_type
    global _enable_color
    if not _enable_color:
        return string
    return CSI + "30;103m" + string + CSI + "49;39m"


def green(string):
    # type: (text_type) -> text_type
    global _enable_color
    if not _enable_color:
        return string
    return CSI + "1;32m" + string + CSI + "39;22m"


def get_string_of_length(string, length):
    # type: (text_type, Optional[int]) -> text_type
    if length is None:
        return string

    initial_length = visual_length(string)
    if initial_length == length:
        return string

    if initial_length < length:
        return string + u' ' * (length - initial_length)

    if initial_length > length:
        return crop_ansi_string_at_length(string, length)

    assert False  # How did we end up here?


def _tokenize(string):
    # type: (text_type) -> Iterable[text_type]
    """
    Tokenizes string into character sequences and ANSI sequences.
    """
    i = 0
    while i < len(string):
        try:
            next_csi_index = string.index(CSI, i)
        except ValueError:
            # No more CSIs
            break
        if next_csi_index > i:
            # Yield char sequence until next CSI marker
            yield string[i:next_csi_index]
            i = next_csi_index
            continue

        # We are at a CSI marker
        try:
            next_m_index = string.index('m', i)
        except ValueError:
            # No end-of-escape sequence found
            break
        next_i = next_m_index + 1

        # Yield full escape sequence
        yield string[i:next_i]
        i = next_i
        continue

    # Yield the remaining part of the string
    yield string[i:]


def crop_ansi_string_at_length(string, length):
    # type: (text_type, int) -> text_type
    assert length >= 0
    if length == 0:
        return ''

    result = u""
    char_count = 0

    reset_sequence = u""

    for token in _tokenize(string):
        if token.startswith(CSI):
            reset_sequence = CSI + '0m'
            if token == reset_sequence:
                # Already reset
                reset_sequence = ""
            result += token
            continue

        # Not a CSI token
        missing_count = length - char_count
        if len(token) >= missing_count:
            result += token[:missing_count]
            break

        result += token
        char_count += len(token)

    return result + reset_sequence


def visual_length(string):
    # type: (text_type) -> int
    """
    If we print this string, possibly containing ANSI characters, to
    screen, how many characters wide will it be?
    """
    count = 0
    for token in _tokenize(string):
        if not token.startswith(CSI):
            # These are characters
            count += len(token)

    return count

def _enter_fullscreen():
    global initial_termios_attr
    assert initial_termios_attr is None

    fd = sys.stdin.fileno()

    initial_termios_attr = termios.tcgetattr(sys.stdin.fileno())

    tty.setraw(fd)


def _exit_fullscreen():
    global initial_termios_attr
    assert initial_termios_attr is not None

    fd = sys.stdin.fileno()
    tty.setcbreak(fd)

    # tty.setraw() disables local echo, so we have to re-enable it here.
    # See the "source code" comment to this answer:
    # http://stackoverflow.com/a/8758047/473672
    if initial_termios_attr:
        termios.tcsetattr(fd, termios.TCSADRAIN, initial_termios_attr)
    initial_termios_attr = None


class fullscreen_display:
    def __enter__(self):
        _enter_fullscreen()
        return None

    def __exit__(self, exception_type, exception_value, exception_traceback):
        _exit_fullscreen()

        # Re-raise any exception:
        # https://docs.python.org/2.5/whatsnew/pep-343.html#context-managers
        return False


class normal_display:
    """
    Pause fullscreen mode
    """

    def __enter__(self):
        _exit_fullscreen()
        return None

    def __exit__(self, exception_type, exception_value, exception_traceback):
        _enter_fullscreen()

        # Re-raise any exception:
        # https://docs.python.org/2.5/whatsnew/pep-343.html#context-managers
        return False
