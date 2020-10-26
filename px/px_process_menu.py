"""
Interactive menu for killing or infoing a process.

Invoked from px_top.py.
"""

import os
import sys
import time
import errno
import signal

from . import px_pager
from . import px_process
from . import px_terminal
from . import px_processinfo

if False:
    # For mypy PEP-484 static typing validation
    from typing import Optional  # NOQA
    from typing import Union     # NOQA


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

        # Shown to user, status of last operation
        self.status = u""

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

        process_line = str(self.process.pid) + u" " + self.process.command
        process_line = px_terminal.get_string_of_length(process_line, columns)
        process_line = px_terminal.inverse_video(process_line)
        lines += [process_line]
        lines += [u""]

        for entry_no, text in enumerate(self.MENU_ENTRIES):
            prefix = u'  '
            if entry_no == self.active_entry:
                prefix = u'->'
                text = px_terminal.bold(text)
            lines += [prefix + text]

        if self.status:
            lines += [u"", u'Status: ' + px_terminal.bold(self.status)]


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

        self.status = u''
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
            elif input.consume(px_terminal.KEY_ESC):
                self.done = True
                return
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

    def isPermissionError(self, e):
        # type: (Union[IOError, OSError]) -> bool
        # Inspired by https://stackoverflow.com/a/18200289/473672
        return e.errno in [errno.EPERM, errno.EACCES]


    def kill_process(self, signo = None):
        # type: (int) -> bool
        """
        Kill process with signal, wait 5s for it to die.

        signo None: Try with SIGTERM, wait 5s, then try SIGKILL
        signo number: Try killing with this signal, wait 5s for process to go away

        Returns: True if the process died, False otherwise
        """

        if signo is None:
            # Please die
            if self.kill_process(signal.SIGTERM):
                return True

            # Die!!
            if self.kill_process(signal.SIGKILL):
                return True

            return False

        try:
            os.kill(self.process.pid, signo)
        except (IOError, OSError) as e:
            if not self.isPermissionError(e):
                raise e

            self.status = u"Not allowed to kill <" + self.process.command + ">, try again as root!"
            return False

        # Give process 5s to die, possibly show a countdown for the duration
        t0 = time.time()
        while (time.time() - t0) < 5:
            if not self.process.is_alive():
                return True

            dt = time.time() - t0
            self.status = u""
            if dt > 1:
                self.status = u"Signal {} did not kill {} after {:.1f}s".format(
                    signo,
                    self.process.command,
                    dt
                )
            self.redraw()

            time.sleep(0.3)

        return False


    def execute_menu_entry(self):
        # NOTE: Constants here must match lines in self.MENU_ENTRIES
        # at the top of this file
        if self.active_entry == 0:
            self.page_process_info()
        elif self.active_entry == 1:
            pass  # FIXME: sudo page_process_info()
        elif self.active_entry == 2:
            if self.kill_process():
                self.done = True
        elif self.active_entry == 3:
            pass  # FIXME: sudo kill_process()
        elif self.active_entry == 4:
            self.done = True
