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
    from typing import Callable  # NOQA
    from typing import Union     # NOQA

KILL_TIMEOUT_SECONDS = 5


def kill(pid, signo):
    # type: (int, int) -> bool
    """
    Signal a process.

    Returns True if the signal was delivered, False otherwise (not allowed).
    """
    try:
        os.kill(pid, signo)
    except (IOError, OSError) as e:
        if e.errno not in [errno.EPERM, errno.EACCES]:
            raise e

        return False

    return True


class PxProcessMenu(object):
    # NOTE: Must match number constants in execute_menu_entry()
    MENU_ENTRIES = [
        u"Show info",
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
        while (not self.done) and (self.process.is_alive()):
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


    def await_death(self, message):
        # type(text_type) -> bool
        """
        Wait KILL_TIMEOUT_SECONDS for process to die.

        Returns True if it did, False if it didn't.
        """
        t0 = time.time()
        while (time.time() - t0) < KILL_TIMEOUT_SECONDS:
            if not self.process.is_alive():
                return True

            dt_s = time.time() - t0
            countdown_s = KILL_TIMEOUT_SECONDS - dt_s
            if countdown_s <= 0:
                break
            self.status = u"{:.1f}s {}".format(
                countdown_s,
                message,
            )
            self.redraw()

            time.sleep(0.1)


    def kill_process(self, signal_process):
        # type: (Callable[[int, int], bool]) -> bool
        """
        Kill process with signal, wait 5s for it to die.

        signo None: Try with SIGTERM, wait 5s, then try SIGKILL
        signo number: Try killing with this signal, wait 5s for process to go away

        Returns: True if the process died, False otherwise
        """

        # Please go away
        if not signal_process(self.process.pid, signal.SIGTERM):
            self.status = u"Not allowed to kill <" + self.process.command + ">, try again as root!"
            return False
        if self.await_death(u"Waiting for %s to shut down after SIGTERM" % self.process.command):
            return True

        # Die!!
        assert signal_process(self.process.pid, signal.SIGKILL)
        if self.await_death(u"Waiting for %s to shut down after kill -9" % self.process.command):
            return True

        self.status = u"<" + self.process.command + "> did not die!"
        return False


    def execute_menu_entry(self):
        # NOTE: Constants here must match lines in self.MENU_ENTRIES
        # at the top of this file
        if self.active_entry == 0:
            self.page_process_info()
        elif self.active_entry == 1:
            self.kill_process(kill)
        elif self.active_entry == 2:
            pass  # FIXME: sudo kill_process()
        elif self.active_entry == 3:
            self.done = True
