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


class PxProcessMenu(object):
    MENU_ENTRIES = [
        u"Show info",
        u"Show info as root",
        u"Kill process",
        u"Kill process as root",
        u"Back to process listing"
    ]

    def __init__(self, process):
        # type: (px_process.PxProcess) -> None
        self.process = process
        self.done = False


    def redraw(self):
        # type: () -> None
        """
        Refresh display.

        The new display will be rows rows x columns columns.
        """
        window_size = px_terminal.get_window_size()
        if window_size is None:
            exit("Cannot find terminal window size, are you on a terminal?\r\n")
        rows, columns = window_size

        lines = [u"Imagine a process menu here " + str(time.time())]
        lines += [u"Process: " + px_terminal.bold(self.process.command)]
        lines += self.MENU_ENTRIES
        px_terminal.draw_screen_lines(lines, True)

    def handle_commands(self):
        # type: () -> None
        """
        Call getch() and interpret the results.

        Returns True if the user requested quit, False otherwise.
        """
        input = px_terminal.getch()
        if input is None:
            return
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
                self.done = True
                return
            elif input.consume(px_terminal.SIGWINCH_KEY):
                return
            else:
                # Unable to consume anything, give up
                break

    def start(self):
        # type: () -> None
        """
        Process menu main loop
        """
        while not self.done:
            self.redraw()
            self.handle_commands()

    def page_process_info(self):
        # type: () -> None
        """
        Display process info in a pager.
        """
        # Is this PID available?
        processes = px_process.get_all()
        process = px_processinfo.find_process_by_pid(self.process.pid, processes)
        if not process:
            # Process not available, never mind
            return

        with px_terminal.normal_display():
            px_pager.page_process_info(process, processes)
