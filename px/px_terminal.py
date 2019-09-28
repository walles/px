import os
import sys
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


def get_window_size():
    # type: () -> Optional[Tuple[int, int]]
    """
    Return the terminal window size as tuple (rows, columns) if available, or
    None if not.
    """

    if not sys.stdout.isatty():
        # We shouldn't truncate lines when piping
        return None

    result = None
    with os.popen('stty size', 'r') as stty_size:
        result = stty_size.read().split()
    if len(result) < 2:
        # Getting the terminal window width failed, don't truncate
        return None

    columns = int(result[1])
    if columns < 1:
        # This seems to happen during OS X CI runs:
        # https://travis-ci.org/walles/px/jobs/113134994
        return None

    rows = int(result[0])
    if rows < 1:
        # Don't know if this actually happens, we just do it for symmetry with
        # the columns check above
        return None

    return (rows, columns)


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
        heading_line = crop_ansi_string_at_length(heading_line, heading_line_delta)

    heading_line = bold(heading_line)
    lines.append(heading_line)

    for proc in procs:
        line = format.format(
            proc.pid, proc.command, proc.username,
            proc.cpu_percent_s, proc.cpu_time_s,
            proc.memory_percent_s, proc.cmdline)
        lines.append(line[0:columns])

    if row_to_highlight is not None:
        # The "+ 1" here is to skip the heading line
        highlighted = lines[row_to_highlight + 1]
        highlighted = get_string_of_length(highlighted, columns)
        highlighted = inverse_video(highlighted)

        # The "+ 1" here is to skip the heading line
        lines[row_to_highlight + 1] = highlighted

    lines[0] = heading_line

    return lines


def inverse_video(string):
    # type: (text_type) -> text_type
    CSI = "\x1b["

    return CSI + "7m" + string + CSI + "27m"


def bold(string):
    # type: (text_type) -> text_type
    CSI = "\x1b["

    return CSI + "1m" + string + CSI + "22m"


def underline(string):
    # type: (text_type) -> text_type
    CSI = "\x1b["

    return CSI + "4m" + string + CSI + "24m"


def get_string_of_length(string, length):
    # type: (text_type, Optional[int]) -> text_type
    if length is None:
        return string

    if len(string) < length:
        return string + (length - len(string)) * ' '

    if len(string) > length:
        return string[0:length]

    return string


def _tokenize(string):
    # type: (text_type) -> Iterable[text_type]
    """
    Tokenizes string into chars and ANSI sequences.
    """
    i = 0
    while i < len(string):
        try:
            char = string[i]
            if char == CSI[0]:
                c0 = i
                while string[i] != 'm':
                    i += 1
                yield string[c0:i + 1]
                continue

            yield string[i]
        finally:
            i += 1


def crop_ansi_string_at_length(string, length):
    # type: (text_type, int) -> text_type
    result = u""
    char_count = 0

    reset_sequence = u""

    for token in _tokenize(string):
        if char_count == length:
            return result + reset_sequence

        if len(token) == 1:
            char_count += 1
        else:
            reset_sequence = CSI + '0m'
            if token == reset_sequence:
                # Already reset
                reset_sequence = ""

        result += token

    return result + reset_sequence


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
