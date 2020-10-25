"""
Interactive menu for killing or infoing a process.

Invoked from px_top.py.
"""

import os
import sys
import time

from . import px_pager
from . import px_process
from . import px_terminal
from . import px_processinfo

if False:
    # For mypy PEP-484 static typing validation
    from typing import Optional  # NOQA


def redraw(
    rows,    # type: int
    columns  # type: int
):
    # type: (...) -> None
    """
    Refresh display.

    The new display will be rows rows x columns columns.
    """

    lines = [u"Imagine a process menu here " + str(time.time())]
    px_terminal.draw_screen_lines(lines, True)


def handle_commands_return_should_quit():
    # type: () -> bool
    """
    Call getch() and interpret the results.

    Returns True if the user requested quit, False otherwise.
    """
    input = px_terminal.getch()
    if input is None:
        return False
    assert len(input) > 0

    while len(input) > 0:
        if input.consume(px_terminal.KEY_UPARROW):
            # FIXME: Move up the menu options
            pass
        elif input.consume(px_terminal.KEY_DOWNARROW):
            # FIXME: Move down the menu options
            pass
        elif input.consume(px_terminal.KEY_ENTER):
            # FIXME: Execute the current menu option
            pass
        elif input.consume(u'q'):
            return True
        elif input.consume(px_terminal.SIGWINCH_KEY):
            return False
        else:
            # Unable to consume anything, give up
            break

    return False


def show_process_menu(pid):
    """
    Process menu main loop
    """
    while True:
        window_size = px_terminal.get_window_size()
        if window_size is None:
            exit("Cannot find terminal window size, are you on a terminal?\r\n")
        rows, columns = window_size
        redraw(rows, columns)

        if handle_commands_return_should_quit():
            return


def page_process_info(pid):
    # type: (Optional[int]) -> None
    """
    Display process info in a pager.
    """
    if pid is None:
        # Nothing selected, never mind
        return

    # Is this PID available?
    processes = px_process.get_all()
    process = px_processinfo.find_process_by_pid(pid, processes)
    if not process:
        # Process not available, never mind
        return

    with px_terminal.normal_display():
        px_pager.page_process_info(process, processes)
