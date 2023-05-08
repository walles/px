import getpass
import os
import sys
import errno
import signal
import select
import termios
import tty

from typing import Dict
from typing import List
from typing import Tuple
from typing import Optional
from typing import Iterable
from . import px_process


# NOTE: To work with this list it can be useful to find the text "Uncomment to
# debug input characters" in handle_search_keypresses() in px_top.py.
KEY_ESC = "\x1b"
KEY_DELETE = "\x1b[3~"
KEY_BACKSPACE = "\x7f"
KEY_UPARROW = "\x1b[A"
KEY_DOWNARROW = "\x1b[B"
KEY_ENTER = "\x0d"


initial_termios_attr = None


CSI = "\x1b["

CURSOR_TO_TOP_LEFT = CSI + "H"
CURSOR_TO_RIGHT_EDGE = CSI + "999C"  # Actually "999 steps to the right"

"""
Clear the screen and move cursor to top left corner:
https://en.wikipedia.org/wiki/ANSI_escape_code

Note that some experimentation was involved in coming up with this
exact sequence; if you do first "clear the full screen" then "home"
for example, the contents of the previous screen gets added to the
scrollback buffer, which isn't what we want. Tread carefully if you
intend to change these.
"""
CLEAR_SCREEN = CSI + "1J" + CURSOR_TO_TOP_LEFT

HIDE_CURSOR = CSI + "?25l"
SHOW_CURSOR = CSI + "?25h"

CLEAR_TO_EOL = CSI + "0K"
CLEAR_TO_END_OF_SCREEN = CSI + "J"  # Clear from cursor to end of screen

# Used for informing our getch() function that a window resize has occurred
SIGWINCH_PIPE = os.pipe()

# We'll report window resize as this key having been pressed.
#
# NOTE: This must be detected as non-printable by handle_search_keypress().
SIGWINCH_KEY = "\x00"

_enable_color = True

previous_screen_lines: List[str] = []
previous_screen_columns: int = 0


def disable_color():
    global _enable_color
    _enable_color = False


def sigwinch_handler(_signum, _frame):
    """Handle window resize signals by telling our getch() function to return"""
    # "r" for "refresh" perhaps? The actual letter doesn't matter, as long as it
    # doesn't collide with anything with some meaning other than "please
    # redraw".
    os.write(SIGWINCH_PIPE[1], SIGWINCH_KEY.encode("utf-8"))


# Subscribe to window size change signals
signal.signal(signal.SIGWINCH, sigwinch_handler)


class ConsumableString:
    def __init__(self, string: str) -> None:
        self._string = string

    def __len__(self):
        return len(self._string)

    def consume(self, to_consume: str) -> bool:
        if not self._string.startswith(to_consume):
            return False

        self._string = self._string[len(to_consume) :]
        return True


def read_select(
    fds: List[int],
    timeout_seconds: Optional[int] = None,
) -> List[int]:
    """Select on any of the fds becoming ready for read, retry on EINTR"""

    # NOTE: If you change this method, you must test running "px --top" and
    # resize the window
    while True:
        try:
            return select.select(fds, [], [], timeout_seconds)[0]
        except OSError as ose:
            if ose.errno == errno.EINTR:
                # EINTR happens when the terminal window is resized by the user,
                # just try again.
                continue

            # Non-EINTR exceptions are unexpected, help!
            raise


def getch(
    timeout_seconds: Optional[int] = None, fd: Optional[int] = None
) -> Optional[ConsumableString]:
    """
    Wait at most timeout_seconds for a character to become available on stdin.

    Returns the character, or None on timeout.
    """
    if fd is None:
        fd = sys.stdin.fileno()

    can_read_from = read_select([fd, SIGWINCH_PIPE[0]], timeout_seconds)

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
    pass


def get_window_size() -> Tuple[int, int]:
    """
    Return the terminal window size as tuple (rows, columns).

    Raises a TerminalError if the window size is unavailable.
    """
    if not sys.stdout.isatty():
        # We shouldn't truncate lines when piping
        raise TerminalError("Not a TTY, window size not available")

    result = None
    with os.popen("stty size", "r") as stty_size:
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


def raw_lines_to_screen_lines(raw_lines: List[str], columns: int) -> List[str]:
    """Crop the lines to the right length and add clear-to-EOL at the end"""
    screen_lines: List[str] = []

    for raw_line in raw_lines:
        cooked = crop_ansi_string_at_length(raw_line, columns)
        cooked += CLEAR_TO_EOL
        screen_lines.append(cooked)

    return screen_lines


def filter_out_unchanged_screen_lines(
    all_screen_lines: List[str], columns: int
) -> List[Optional[str]]:
    """Compare lines to the cache and None out the ones that match the cache"""

    if len(previous_screen_lines) != len(all_screen_lines):
        # Screen resized, never mind the cache
        return all_screen_lines  # type: ignore
    if previous_screen_columns != columns:
        # Screen resized, never mind the cache
        return all_screen_lines  # type: ignore

    filtered: List[Optional[str]] = []
    for line_index, line in enumerate(all_screen_lines):
        line_from_previous_screen = previous_screen_lines[line_index]
        if line == line_from_previous_screen:
            # Cache hit, don't draw this line
            filtered.append(None)
        else:
            filtered.append(line)

    return filtered


def draw_screen_lines(lines: List[str], columns: int) -> None:
    unfiltered_screen_lines = raw_lines_to_screen_lines(lines, columns)
    screen_lines = filter_out_unchanged_screen_lines(unfiltered_screen_lines, columns)

    screenstring = CURSOR_TO_TOP_LEFT
    skip_lines = 0
    for screen_line in screen_lines:
        if screen_line is None:
            skip_lines += 1
        else:
            if skip_lines > 0:
                # Move down the required number of lines
                screenstring += CSI + str(skip_lines) + "E"
                skip_lines = 0

            # The line changed, update it!
            screenstring += screen_line

            # Move to next line
            skip_lines = 1

    if skip_lines > 1:
        # Move down the required number of lines. "- 1" because if we skip after
        # the last line, there'll be a leftover line when we enter the
        # per-process menu.
        screenstring += CSI + str(skip_lines - 1) + "E"
        skip_lines = 0

    # Keep the cache up to date
    global previous_screen_lines
    global previous_screen_columns
    previous_screen_lines = unfiltered_screen_lines
    previous_screen_columns = columns

    # In case we got fewer lines than what fits on screen, clear the rest of it.
    # We must start at the right edge of screen doing this in case differential
    # rendering made us not do anything for the last screen line.
    screenstring += CURSOR_TO_RIGHT_EDGE + CLEAR_TO_END_OF_SCREEN

    os.write(sys.stdout.fileno(), screenstring.encode("utf-8"))


def width_specifier(width: int, right_align: bool = False) -> str:
    return_me = "{:"

    if right_align:
        return_me += ">"

    return_me += str(width)
    return_me += "}"

    return return_me


def format_with_widths(widths: List[int], strings: List[str]) -> str:
    """
    Put strings next to each other with a space between each.

    Negative column widths means right aligned text.

    Zero width columns are unlimited.
    """

    assert len(widths) == len(strings)

    result = ""
    for i, width in enumerate(widths):
        if i > 0:
            result += " "

        string = strings[i]

        if width == 0:
            result += string
            continue

        padding_amount = abs(width) - visual_length(string)
        if padding_amount <= 0:
            # NOTE: Future improvement: Crop here rather than just pretending
            # everything is fine
            result += string
            continue

        padding = padding_amount * " "
        if width > 0:
            result += string + padding
        else:
            # Right align
            result += padding + string

    return result


def to_screen_lines(
    procs: List[px_process.PxProcess],
    row_to_highlight: Optional[int],
    highlight_heading: Optional[str],
    with_username: bool = True,
) -> List[str]:
    """
    Returns an array of lines that can be printed to screen. Lines are not
    cropped, so they can be longer than the screen width.

    If highligh_heading contains a column name, that column will be highlighted.
    The column name must be from the hard coded list in this function, see below.
    """

    headings = [
        "PID",
        "COMMAND",
        "USERNAME",
        "CPU",
        "CPUTIME",
        "RAM",
        "COMMANDLINE",
    ]
    highlight_column: Optional[int] = None
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

    column_widths = [
        -pid_width,
        command_width,
        username_width,
        -cpu_width,
        -cputime_width,
        -mem_width,
        0,  # The command line can have any length
    ]

    if not with_username:
        username_index = headings.index("USERNAME")
        del headings[username_index]
        del column_widths[username_index]

    # Print process list using the computed column widths
    lines = []

    # Highlight the highlight_column
    if highlight_column is not None:
        headings[highlight_column] = underline(headings[highlight_column])

    heading_line = format_with_widths(column_widths, headings)
    heading_line = bold(heading_line)
    lines.append(heading_line)

    max_cpu_percent_s: Optional[str] = None
    max_cpu_percent = 0.0
    max_memory_percent_s: Optional[str] = None
    max_memory_percent = 0.0
    max_cpu_time_seconds = 0.0
    for proc in procs:
        if proc.cpu_percent is not None and proc.cpu_percent > max_cpu_percent:
            max_cpu_percent = proc.cpu_percent
            max_cpu_percent_s = proc.cpu_percent_s
        if proc.memory_percent is not None and proc.memory_percent > max_memory_percent:
            max_memory_percent = proc.memory_percent
            max_memory_percent_s = proc.memory_percent_s
        if (
            proc.cpu_time_seconds is not None
            and proc.cpu_time_seconds > max_cpu_time_seconds
        ):
            max_cpu_time_seconds = proc.cpu_time_seconds

    current_user = os.environ.get("SUDO_USER") or getpass.getuser()
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
        if not proc.cpu_time_seconds:
            # Zero or undefined
            cpu_time_s = faint(cpu_time_s.rjust(cputime_width))
        elif proc.cpu_time_seconds > 0.75 * max_cpu_time_seconds:
            cpu_time_s = bold(cpu_time_s.rjust(cputime_width))
        elif proc.cpu_time_seconds < 0.1 * max_cpu_time_seconds:
            cpu_time_s = faint(cpu_time_s.rjust(cputime_width))

        # NOTE: This logic should match its friend in
        # px_processinfo.py/print_process_tree()
        owner = proc.username
        if owner == "root":
            owner = faint(owner)
        elif owner != current_user:
            # Neither root nor ourselves, highlight!
            owner = bold(owner)

        columns = [
            str(proc.pid),
            proc.command,
            owner,
            cpu_percent_s,
            cpu_time_s,
            memory_percent_s,
            proc.cmdline,
        ]
        if not with_username:
            del columns[username_index]
        line = format_with_widths(column_widths, columns)

        if row_to_highlight == line_number:
            # Highlight the whole screen line
            line = inverse_video(line + " " * 999)
        lines.append(line)

    lines[0] = heading_line

    return lines


def inverse_video(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "7m" + string + CSI + "27m"


def bold(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "1m" + string + CSI + "22m"


def faint(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "2m" + string + CSI + "22m"


def underline(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "4m" + string + CSI + "24m"


def red(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "1;97;41m" + string + CSI + "49;39;22m"


def yellow(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "30;103m" + string + CSI + "49;39m"


def green(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "1;32m" + string + CSI + "39;22m"


def blue(string: str) -> str:
    if not _enable_color:
        return string
    return CSI + "1;97;44m" + string + CSI + "49;39;22m"


def get_string_of_length(string: str, length: Optional[int]) -> str:
    if length is None:
        return string

    initial_length = visual_length(string)
    if initial_length == length:
        return string

    if initial_length < length:
        return string + " " * (length - initial_length)

    if initial_length > length:
        return crop_ansi_string_at_length(string, length)

    assert False  # How did we end up here?


def _tokenize(string: str) -> Iterable[str]:
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
            next_m_index = string.index("m", i)
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


crop_cache: Dict[Tuple[str, int], str] = {}


def crop_ansi_string_at_length(string: str, length: int) -> str:
    assert length >= 0

    cache_key = (string, length)
    cache_hit = crop_cache.get(cache_key, None)
    if cache_hit is not None:
        return cache_hit
    if len(crop_cache) > 400:
        # LRU would be better but this is easier to implement
        crop_cache.clear()

    result = ""
    char_count = 0

    reset_sequence = ""

    for token in _tokenize(string):
        if token.startswith(CSI):
            reset_sequence = CSI + "0m"
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

    cache_hit = result + reset_sequence
    crop_cache[cache_key] = cache_hit
    return cache_hit


def visual_length(string: str) -> int:
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

    os.write(fd, HIDE_CURSOR.encode("utf-8"))


def _exit_fullscreen():
    global initial_termios_attr
    assert initial_termios_attr is not None

    fd = sys.stdin.fileno()
    os.write(fd, SHOW_CURSOR.encode("utf-8"))

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

    def __exit__(self, exception_type, exception_value, exception_traceback):
        _enter_fullscreen()

        # Re-raise any exception:
        # https://docs.python.org/2.5/whatsnew/pep-343.html#context-managers
        return False
