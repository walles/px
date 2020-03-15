#!/usr/bin/env python3

"""Run multiple command lines in parallel

Syntax: parallelize.py <command line> ...

Example: parallelize.py "runtests1.sh" "runtests2.sh"

This scripts runs multiple command lines in parallel, but presents the result as
if they were run in sequence. So if the first one fails, then we will exit with
the exit code of that first command line, and just terminate the following ones
in the background and pretend we never started them.
"""

import subprocess
import tempfile
import termios
import atexit
import select
import shutil
import fcntl
import pty
import sys
import os


from typing import Dict, List, Optional


PUMP_BUFFER_SIZE = 16384


if len(sys.argv) < 2:
    # One is the executable (this script) name, the rest are command lines
    print("ERROR: Need at least one, but suggest at least two command lines to run")
    print()
    print(__doc__)
    sys.exit(1)


class WrappedProcess:
    def __init__(self, commandline: str):
        self.commandline = commandline

        self.output = tempfile.NamedTemporaryFile()
        atexit.register(self.cleanup)

        pty_in, pty_out = self.get_terminalized_pipe()
        self.pty_out = pty_out

        # FIXME: Set stdin to pipe in from nowhere
        self.process = subprocess.Popen(
            commandline, bufsize=-1, stdout=pty_in, stderr=pty_in, shell=True)

    def get_terminalized_pipe(self):
        """
        Get a pipe-like object where the input end pretends to be a terminal.
        """
        window_size = b'\0' * 4
        # Get terminal window dimensions from stdout
        fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, window_size, True)

        pty_in, pty_out = pty.openpty()

        fcntl.ioctl(pty_in, termios.TIOCSWINSZ, window_size, False)
        return pty_in, pty_out

    def cleanup(self):
        # This implicitly deletes the temp file
        self.output.close()


def pump(processes: List[WrappedProcess], current_process: Optional[WrappedProcess], timeout_seconds=0.2) -> None:
    fd_to_wrapper: Dict[int, WrappedProcess] = {}
    for process in processes:
        fd_to_wrapper[process.pty_out] = process

    r, w, x = select.select(list(fd_to_wrapper.keys()), [], [], timeout_seconds)
    for fd in r:
        process = fd_to_wrapper[fd]
        data = os.read(process.pty_out, PUMP_BUFFER_SIZE)
        if process is current_process:
            os.write(sys.stdout.fileno(), data)
        else:
            process.output.write(data)


commands = sys.argv[1:]
processes = []

for command in commands:
    processes.append(WrappedProcess(command))

process_index = 0
# Only enter this loop if we have processes to process
while processes:
    current_process = processes[process_index]
    pump(processes, current_process)

    exitcode = current_process.process.poll()
    if exitcode is None:
        continue

    # Our process died, make sure we got all its output
    pump(processes, current_process, timeout_seconds=0)

    if exitcode == 0:
        process_index += 1
        if process_index >= len(processes):
            break
        current_process = processes[process_index]

        # Dump the new process_index process' tempfile to stdout
        current_process.output.flush()
        with open(current_process.output.name, "r") as f:
            shutil.copyfileobj(f, sys.stdout)

        continue

    # Current process failed, terminate remaining processes
    for killme in processes:
        if killme.process.returncode is not None:
            # Already dead
            continue

        sys.stderr.write("Terminating remaining process: {}\n".format(killme.commandline))
        killme.process.terminate()

    for waitme in processes:
        # If we don't keep the pipes empty processes might freeze, and I don't
        # know whether they would ever shut down in that case.
        while waitme.process.poll() is None:
            pump(processes, None)

    sys.exit(exitcode)
