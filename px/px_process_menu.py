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

from typing import Callable

# Constants signal.SIGXXX are enums in Python 3. But we want the numbers (to
# pass as an argument to /bin/kill), so we make our own int constants.
SIGTERM = 15
SIGKILL = 9

KILL_TIMEOUT_SECONDS = 5


def get_header_line(process: px_process.PxProcess) -> str:
    header_line = "Process: "
    header_line += str(process.pid) + " " + process.command
    header_line = px_terminal.bold(header_line)
    return header_line


def kill(process: px_process.PxProcess, signo: int) -> bool:
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


def sudo_kill(process: px_process.PxProcess, signo: int) -> bool:
    """
    Signal a process as root.

    Returns True if the signal was delivered, False otherwise.
    """
    with px_terminal.normal_display():
        print(px_terminal.CLEAR_SCREEN)

        # Print process screen heading followed by an empty line
        _, columns = px_terminal.get_window_size()

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


class PxProcessMenu:
    # NOTE: Must match number constants in execute_menu_entry()
    MENU_ENTRIES = [
        "Show info",
        "Kill process",
        "Kill process as root",
        "Back to process listing",
    ]

    def __init__(self, process: px_process.PxProcess) -> None:
        self.process = process
        self.done = False

        # Shown to user, status of last operation
        self.status = ""

        # Index into MENU_ENTRIES
        self.active_entry = 0

    def refresh_display(self) -> None:
        _, columns = px_terminal.get_window_size()

        lines = []

        lines += [get_header_line(self.process)]
        lines += [""]

        lines += [
            px_terminal.bold("Arrow keys")
            + " move up and down, "
            + px_terminal.bold("RETURN")
            + " selects, "
            + px_terminal.bold("ESC")
            + " to go back."
        ]
        lines += [""]

        last_entry_no = len(self.MENU_ENTRIES) - 1
        for entry_no, text in enumerate(self.MENU_ENTRIES):
            prefix = "    "
            arrow = "⇵"
            if entry_no == 0:
                arrow = "↓"
            elif entry_no == last_entry_no:
                arrow = "↑"
            if entry_no == self.active_entry:
                prefix = arrow + " ->"
                text = px_terminal.inverse_video(text)

            lines += [prefix + text]

        if self.status:
            lines += ["", "Status: " + px_terminal.bold(self.status)]

        px_terminal.draw_screen_lines(lines, columns)

    def await_and_handle_user_input(self) -> None:
        incoming = px_terminal.getch()
        if incoming is None:
            return
        assert len(incoming) > 0

        self.status = ""
        while len(incoming) > 0:
            if incoming.consume(px_terminal.KEY_UPARROW):
                self.active_entry -= 1
                if self.active_entry < 0:
                    self.active_entry = 0
            elif incoming.consume(px_terminal.KEY_DOWNARROW):
                self.active_entry += 1
                if self.active_entry >= len(self.MENU_ENTRIES):
                    self.active_entry = len(self.MENU_ENTRIES) - 1
            elif incoming.consume(px_terminal.KEY_ENTER):
                self.execute_menu_entry()
            elif incoming.consume("q"):
                self.done = True
                return
            elif incoming.consume(px_terminal.SIGWINCH_KEY):
                # After we return the screen will be refreshed anyway,
                # no need to do anything here.
                continue
            elif incoming.consume(px_terminal.KEY_ESC):
                self.done = True
                return
            else:
                # Unable to consume, give up
                break

    def start(self) -> None:
        """
        Process menu main loop
        """
        while (not self.done) and (self.process.is_alive()):
            self.refresh_display()
            self.await_and_handle_user_input()

    def page_process_info(self) -> None:
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
        # type(str) -> None
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
            self.status = f"{countdown_s:.1f}s {message}"
            self.refresh_display()

            time.sleep(0.1)

    def kill_process(
        self, signal_process: Callable[[px_process.PxProcess, int], bool]
    ) -> None:
        """
        Send first SIGTERM then SIGKILL to a process.

        Wait KILL_TIMEOUT_SECONDS secods in between to give it a chance to go away.
        """

        # Please go away
        if not signal_process(self.process, SIGTERM):
            self.status = (
                "Not allowed to kill <" + self.process.command + ">, try again as root!"
            )
            return
        self.await_death(
            f"Waiting for {self.process.command} to shut down after SIGTERM"
        )
        if not self.process.is_alive():
            return

        # Die!!
        assert signal_process(self.process, SIGKILL)
        self.await_death(
            f"Waiting for {self.process.command} to shut down after kill -9"
        )
        if not self.process.is_alive():
            return

        self.status = "<" + self.process.command + "> did not die!"
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
