# coding=utf-8

"""
Interactive menu for killing or infoing a process.

Invoked from px_top.py.
"""

import os
import time
import errno
import subprocess

from . import px_pager
from . import px_process
from . import px_terminal
from . import px_processinfo

if False:
    # For mypy PEP-484 static typing validation
    from typing import Optional  # NOQA
    from typing import Callable  # NOQA
    from typing import Union  # NOQA
    from six import text_type  # NOQA

# Constants signal.SIGXXX are ints in Python 2 and enums in Python 3.
# Make our own guaranteed-to-be-int constants.
SIGTERM = 15
SIGKILL = 9

KILL_TIMEOUT_SECONDS = 5


def get_header_line(process):
    # type: (px_process.PxProcess) -> text_type
    header_line = u"Process: "
    header_line += str(process.pid) + u" " + process.command
    header_line = px_terminal.bold(header_line)
    return header_line


def kill(process, signo):
    # type: (px_process.PxProcess, int) -> bool
    """
    Signal a process.

    Returns True if the signal was delivered, False otherwise (not allowed).
    """
    try:
        os.kill(process.pid, signo)
    except (IOError, OSError) as e:
        if e.errno not in [errno.EPERM, errno.EACCES]:
            raise e

        return False

    return True


def sudo_kill(process, signo):
    # type: (px_process.PxProcess, int) -> bool
    """
    Signal a process as root.

    Returns True if the signal was delivered, False otherwise.
    """
    with px_terminal.normal_display():
        print(px_terminal.CLEAR_SCREEN)

        # Print process screen heading followed by an empty line
        rows, columns = px_terminal.get_window_size()

        print(px_terminal.crop_ansi_string_at_length(get_header_line(process), columns))
        print("")

        # Print "sudo kill 1234"
        command = ["sudo", "kill"]
        if signo != SIGTERM:
            command += ["-" + str(signo)]
        command += [str(process.pid)]

        print("$ " + " ".join(command))

        # Invoke "sudo kill 1234"
        returncode = subprocess.call(command)
        if returncode == 0:
            return True

        # Give user time to peruse any error message
        time.sleep(1.5)
        return False


class PxProcessMenu(object):
    # NOTE: Must match number constants in execute_menu_entry()
    MENU_ENTRIES = [
        u"Show info",
        u"Kill process",
        u"Kill process as root",
        u"Back to process listing",
    ]

    def __init__(self, process):
        # type: (px_process.PxProcess) -> None
        self.process = process
        self.done = False

        # Shown to user, status of last operation
        self.status = u""

        # Index into MENU_ENTRIES
        self.active_entry = 0

    def refresh_display(self):
        # type: () -> None
        rows, columns = px_terminal.get_window_size()

        lines = []

        lines += [get_header_line(self.process)]
        lines += [u""]

        lines += [
            px_terminal.bold("Arrow keys")
            + " move up and down, "
            + px_terminal.bold("RETURN")
            + " selects, "
            + px_terminal.bold("ESC")
            + " to go back."
        ]
        lines += [u""]

        last_entry_no = len(self.MENU_ENTRIES) - 1
        for entry_no, text in enumerate(self.MENU_ENTRIES):
            prefix = u"    "
            arrow = u"⇵"
            if entry_no == 0:
                arrow = u"↓"
            elif entry_no == last_entry_no:
                arrow = u"↑"
            if entry_no == self.active_entry:
                prefix = arrow + u" ->"
                text = px_terminal.inverse_video(text)

            lines += [prefix + text]

        if self.status:
            lines += [u"", u"Status: " + px_terminal.bold(self.status)]

        px_terminal.draw_screen_lines(lines, columns)

    def await_and_handle_user_input(self):
        # type: () -> None
        input = px_terminal.getch()
        if input is None:
            return
        assert len(input) > 0

        self.status = u""
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
            elif input.consume(u"q"):
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
            self.refresh_display()
            self.await_and_handle_user_input()

    def page_process_info(self):
        # type: () -> None
        """
        Display process info in a pager.
        """
        processes = px_process.get_all()
        process = px_processinfo.find_process_by_pid(self.process.pid, processes)
        if not process:
            # Process not available, never mind
            return

        with px_terminal.normal_display():
            px_pager.page_process_info(process, processes)

    def await_death(self, message):
        # type(text_type) -> None
        """
        Wait KILL_TIMEOUT_SECONDS for process to die.

        Returns after either the process dies or we run out of time,
        whichever comes first.
        """
        t0 = time.time()
        while (time.time() - t0) < KILL_TIMEOUT_SECONDS:
            if not self.process.is_alive():
                return

            dt_s = time.time() - t0
            countdown_s = KILL_TIMEOUT_SECONDS - dt_s
            if countdown_s <= 0:
                return
            self.status = u"{:.1f}s {}".format(
                countdown_s,
                message,
            )
            self.refresh_display()

            time.sleep(0.1)

    def kill_process(self, signal_process):
        # type: (Callable[[px_process.PxProcess, int], bool]) -> None
        """
        Send first SIGTERM then SIGKILL to a process.

        Wait KILL_TIMEOUT_SECONDS secods in between to give it a chance to go away.
        """

        # Please go away
        if not signal_process(self.process, SIGTERM):
            self.status = (
                u"Not allowed to kill <"
                + self.process.command
                + ">, try again as root!"
            )
            return
        self.await_death(
            u"Waiting for %s to shut down after SIGTERM" % self.process.command
        )
        if not self.process.is_alive():
            return

        # Die!!
        assert signal_process(self.process, SIGKILL)
        self.await_death(
            u"Waiting for %s to shut down after kill -9" % self.process.command
        )
        if not self.process.is_alive():
            return

        self.status = u"<" + self.process.command + "> did not die!"
        return

    def execute_menu_entry(self):
        # NOTE: Constants here must match lines in self.MENU_ENTRIES
        # at the top of this file
        if self.active_entry == 0:
            self.page_process_info()
        elif self.active_entry == 1:
            self.kill_process(kill)
        elif self.active_entry == 2:
            self.kill_process(sudo_kill)
        elif self.active_entry == 3:
            self.done = True
