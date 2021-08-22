# coding=utf-8

import sys
import copy
import time
import logging
import unicodedata

import os
from . import px_process
from . import px_terminal
from . import px_processinfo
from . import px_process_menu
from . import px_poller

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List  # NOQA
    from typing import Dict  # NOQA
    from typing import Union  # NOQA
    from typing import Optional  # NOQA
    from six import text_type  # NOQA

LOG = logging.getLogger(__name__)

CMD_WHATEVER = -1
CMD_QUIT = 1
CMD_RESIZE = 2
CMD_HANDLED = 3
CMD_POLL_COMPLETE = 4

SEARCH_PROMPT_ACTIVE = px_terminal.inverse_video("Search (ENTER when done): ")
SEARCH_PROMPT_INACTIVE = "Search ('/' to edit): "
SEARCH_CURSOR = px_terminal.inverse_video(" ")

MODE_BASE = 0
MODE_SEARCH = 1

top_mode = MODE_BASE  # type: int
search_string = u""

# Which pid were we last hovering?
last_highlighted_pid = None  # type: Optional[int]

# Which row were we last hovering? Go for this one if
# we can't use last_pid.
last_highlighted_row = 0  # type: int

# Has the user manually moved the highlight? If not, just stay on the top
# row even if the tow PID moves away.
highlight_has_moved = False  # type: bool

# Order top list by memory usage. The opposite is by CPU usage.
sort_by_memory = False


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
        if current_proc.cpu_time_seconds and baseline_proc.cpu_time_seconds:
            current_proc.set_cpu_time_seconds(
                current_proc.cpu_time_seconds - baseline_proc.cpu_time_seconds
            )
        pid2proc[current_proc.pid] = current_proc

    return list(pid2proc.values())


def get_notnone_cpu_time_seconds(proc):
    # type: (px_process.PxProcess) -> float
    seconds = proc.cpu_time_seconds
    if seconds is not None:
        return seconds
    return 0


def get_notnone_memory_percent(proc):
    # type: (px_process.PxProcess) -> float
    percent = proc.memory_percent
    if percent is not None:
        return percent
    return 0


def sort_by_cpu_usage(toplist):
    # type(List[px_process.PxProcess]) -> List[px_process.PxProcess]
    can_sort_by_time = False
    for process in toplist:
        if process.cpu_time_seconds:
            can_sort_by_time = True
            break

    if can_sort_by_time:
        # There is at least one > 0 time in the process list, so sorting by time
        # will be of some use
        return sorted(toplist, key=get_notnone_cpu_time_seconds, reverse=True)

    # No > 0 time in the process list, try CPU percentage as an approximation of
    # that. This should happen on the first iteration when ptop has just been
    # launched.
    return sorted(toplist, key=lambda process: process.cpu_percent or 0, reverse=True)


def get_toplist(
    baseline,  # type: List[px_process.PxProcess]
    current,  # type: List[px_process.PxProcess]
    by_memory=False,  # type: bool
):
    # type(...) -> List[px_process.PxProcess]
    toplist = adjust_cpu_times(baseline, current)

    # Sort by interestingness last
    toplist = px_process.order_best_first(toplist)
    if by_memory:
        toplist = sorted(toplist, key=get_notnone_memory_percent, reverse=True)
    else:
        # By CPU time, this is the default
        toplist = sort_by_cpu_usage(toplist)

    return toplist


def writebytes(bytestring):
    # type: (bytes) -> None
    os.write(sys.stdout.fileno(), bytestring)


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
        last_highlighted_row, max_process_count - 1, len(toplist) - 1
    )
    if last_highlighted_row < 0:
        last_highlighted_row = 0

    if last_highlighted_row > 0:
        highlight_has_moved = True

    # Stay on the top line unless the user has explicitly moved the highlight
    last_highlighted_pid = toplist[last_highlighted_row].pid

    return last_highlighted_row


def get_screen_lines(
    toplist,  # type: List[px_process.PxProcess]
    poller,  # type: px_poller.PxPoller
    rows,  # type: int
    include_footer=True,  # type: bool
    search=None,  # type: Optional[text_type]
):
    # type: (...) -> List[text_type]

    if search:
        # Note that we accept partial user name match, otherwise incrementally typing
        # a username becomes weird for the ptop user
        toplist = list(
            filter(lambda p: p.match(search, require_exact_user=False), toplist)
        )

    # Hand out different amount of lines to the different sections
    footer_height = 0
    cputop_minheight = 10
    if include_footer:
        footer_height = 1

    # Print header
    lines = [
        px_terminal.bold(u"Sysload: ") + poller.get_loadstring(),
        px_terminal.bold(u"RAM Use: ") + poller.get_meminfo(),
        px_terminal.bold(u"IO Load:      ") + poller.get_ioload_string(),
        u"",
    ]

    # Create a launchers section
    header_height = len(lines)
    launches_maxheight = rows - header_height - cputop_minheight - footer_height
    launchlines = []  # type: List[text_type]
    if launches_maxheight >= 3:
        launchlines = poller.get_launchcounter_lines()
        if len(launchlines) > 0:
            # Add a section header
            launchlines = [
                "",
                px_terminal.bold("Launched binaries, launch counts in (parentheses)"),
            ] + launchlines

            # Cut if we got too many lines
            launchlines = launchlines[0:launches_maxheight]

    # Compute cputop height now that we know how many launchlines we have
    cputop_height = rows - header_height - len(launchlines) - footer_height

    # -2 = Section name + column headings
    max_process_count = cputop_height - 2

    # Search prompt needs one line
    max_process_count -= 1

    highlight_row = get_line_to_highlight(toplist, max_process_count)
    global top_mode
    if top_mode == MODE_SEARCH:
        highlight_row = None

    highlight_column = u"CPUTIME"
    if sort_by_memory:
        highlight_column = u"RAM"
    toplist_table_lines = px_terminal.to_screen_lines(
        toplist[:max_process_count], highlight_row, highlight_column
    )

    # Ensure that we cover the whole screen, even if it's higher than the
    # number of processes
    toplist_table_lines += rows * [""]

    top_what = "CPU"
    if sort_by_memory:
        top_what = "memory"
    lines += [px_terminal.bold("Top " + top_what + " using processes")]

    if top_mode == MODE_SEARCH:
        lines += [SEARCH_PROMPT_ACTIVE + px_terminal.bold(search or "") + SEARCH_CURSOR]
    else:
        assert top_mode == MODE_BASE
        lines += [SEARCH_PROMPT_INACTIVE + px_terminal.bold(search or "")]

    lines += toplist_table_lines[
        0 : max_process_count + 1
    ]  # +1 for the column headings

    lines += launchlines

    if include_footer:
        footer_line = (
            u"  q - Quit  m - Sort order  / - Search  ↑↓ - Move  Enter - Select"
        )
        # Inverse the whole footer line
        footer_line = px_terminal.inverse_video(footer_line + 999 * u" ")

        lines += [footer_line]

    return lines


def redraw(
    toplist,  # type: List[px_process.PxProcess]
    poller,  # type: px_poller.PxPoller
    rows,  # type: int
    columns,  # type: int
    include_footer=True,  # type: bool
):
    # type: (...) -> None
    """
    Refresh display.

    The new display will be rows rows x columns columns.
    """
    global search_string
    lines = get_screen_lines(
        toplist, poller, rows, include_footer, search=search_string
    )

    px_terminal.draw_screen_lines(lines, columns)


def handle_search_keypresses(key_sequence):
    # type: (px_terminal.ConsumableString) -> None
    global search_string
    global last_highlighted_row
    global last_highlighted_pid

    # If this triggers our top_mode state machine is broken
    assert search_string is not None

    # NOTE: Uncomment to debug input characters
    # search_string = ":".join("{:02x}".format(ord(c)) for c in key_sequence._string)
    # return

    while len(key_sequence) > 0:
        if key_sequence.consume(px_terminal.KEY_BACKSPACE):
            search_string = search_string[:-1]
        elif key_sequence.consume(px_terminal.KEY_DELETE):
            search_string = search_string[:-1]
        elif key_sequence.consume(px_terminal.KEY_UPARROW):
            last_highlighted_row -= 1
            last_highlighted_pid = None
        elif key_sequence.consume(px_terminal.KEY_DOWNARROW):
            last_highlighted_row += 1
            last_highlighted_pid = None
        elif (
            key_sequence.consume(px_terminal.KEY_ENTER)
            or key_sequence._string == px_terminal.KEY_ESC
        ):
            # Exit search mode
            global top_mode
            top_mode = MODE_BASE
            return
        else:
            # Unable to consume more, give up
            break

    if len(key_sequence) == 0:
        return

    if px_terminal.KEY_ESC in key_sequence._string:
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
    input = px_terminal.getch(**kwargs)
    if input is None:
        return None
    assert len(input) > 0

    global top_mode
    if top_mode == MODE_SEARCH:
        handle_search_keypresses(input)
        return CMD_HANDLED

    global last_highlighted_row
    global last_highlighted_pid
    global sort_by_memory
    while len(input) > 0:
        if input.consume(px_terminal.KEY_UPARROW):
            last_highlighted_row -= 1
            last_highlighted_pid = None
        elif input.consume(px_terminal.KEY_DOWNARROW):
            last_highlighted_row += 1
            last_highlighted_pid = None
        elif input.consume(px_terminal.KEY_ENTER):
            if last_highlighted_pid is None:
                continue
            processes = px_process.get_all()
            process = px_processinfo.find_process_by_pid(
                last_highlighted_pid, processes
            )
            if not process:
                continue
            px_process_menu.PxProcessMenu(process).start()
        elif input.consume(u"/"):
            global search_string
            top_mode = MODE_SEARCH
            return None
        elif input.consume(u"m") or input.consume(u"M"):
            sort_by_memory = not sort_by_memory
        elif input.consume(u"q"):
            return CMD_QUIT
        elif input.consume(px_terminal.SIGWINCH_KEY):
            return CMD_RESIZE
        elif input.consume(px_poller.POLL_COMPLETE_KEY):
            return CMD_POLL_COMPLETE
        else:
            # Unable to consume anything, give up
            break

    return CMD_WHATEVER


def _top(search=""):
    # type: (str) -> None

    global search_string
    search_string = search

    poller = px_poller.PxPoller(px_terminal.SIGWINCH_PIPE[1])
    poller.start()

    baseline = poller.get_all_processes()
    current = poller.get_all_processes()

    global sort_by_memory
    toplist = get_toplist(baseline, current, sort_by_memory)

    rows, columns = px_terminal.get_window_size()

    while True:
        redraw(toplist, poller, rows, columns)

        command = get_command()

        # Handle all keypresses before refreshing the display
        if command is not None:
            poller.pause_process_updates_a_bit()
            if command == CMD_QUIT:
                # The idea here is that if you terminate with "q" you still
                # probably want the heading line on screen. So just do another
                # update with somewhat fewer lines, and you'll get just that.
                redraw(toplist, poller, rows - 4, columns, include_footer=False)
                return

            if command == CMD_RESIZE:
                rows, columns = px_terminal.get_window_size()

            if command == CMD_POLL_COMPLETE:
                current = poller.get_all_processes()
                toplist = get_toplist(baseline, current, sort_by_memory)


def top(search=""):
    # type: (str) -> None

    if not sys.stdout.isatty():
        sys.stderr.write(
            'Top mode only works on TTYs, try running just "px" instead.\n'
        )
        exit(1)

    with px_terminal.fullscreen_display():
        try:
            _top(search=search)
        except Exception:
            LOG.exception("Running ptop failed")

        # Make sure we actually end up on a new line
        print("")
