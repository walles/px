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
    # NOTE: Must match number constants in execute_menu_entry()
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

        # Index into MENU_ENTRIES
        self.active_entry = 0


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

        lines = []
        lines += [u"Process: " + px_terminal.bold(self.process.command)]
        lines += [u""]

        for entry_no, text in enumerate(self.MENU_ENTRIES):
            prefix = u'  '
            if entry_no == self.active_entry:
                prefix = u'->'
            lines += [prefix + text]

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
                self.active_entry -= 1
                if self.active_entry < 0:
                    self.active_entry = 0
            elif input.consume(px_terminal.KEY_DOWNARROW):
                self.active_entry += 1
                if self.active_entry >= len(self.MENU_ENTRIES):
                    self.active_entry = len(self.MENU_ENTRIES) - 1
            elif input.consume(px_terminal.KEY_ENTER):
                self.execute_menu_entry()
            elif input.consume(u'q'):
                self.done = True
                return
            elif input.consume(px_terminal.SIGWINCH_KEY):
                # After we return the screen will be refreshed anyway,
                # no need to do anything here.
                continue
            else:
                # Unable to consume, give up
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

    def execute_menu_entry(self):
        # NOTE: Constants here must match lines in self.MENU_ENTRIES
        # at the top of this file
        if self.active_entry == 0:
            self.page_process_info()
        elif self.active_entry == 1:
            pass  # FIXME: sudo page_process_info()
        elif self.active_entry == 2:
            pass  # FIXME: kill_process()
        elif self.active_entry == 3:
            pass  # FIXME: sudo kill_process()
        elif self.active_entry == 4:
            self.done = True
