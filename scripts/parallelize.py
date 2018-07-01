#!/usr/bin/env python

"""Run multiple command lines in parallel

Syntax: parallelize.py <command line> ...

This scripts runs multiple command lines in parallel, but presents the result as
if they were run in sequence. So if the first one fails, then we will exit with
the exit code of that first command line, and just terminate the following ones
in the background and pretend we never started them.
"""

import subprocess
import tempfile
import atexit
import shutil
import sys


if len(sys.argv) < 2:
    # One is the executable (this script) name, the rest are command lines
    print("ERROR: Need at least one, but suggest at least two command lines to run")
    print()
    print(__doc__)
    sys.exit(1)


class WrappedProcess:
    def __init__(self, cmdline):
        self.output = tempfile.NamedTemporaryFile()
        atexit.register(self.cleanup)

        # FIXME: Trick wrapped process that it's writing to a terminal. Possible
        # source of inspiration:
        # http://man7.org/tlpi/code/online/dist/pty/unbuffer.c.html

        # FIXME: Set stdin to pipe in from nowhere
        self.process = subprocess.Popen(
            cmdline, bufsize=-1, stdout=self.output, stderr=self.output, shell=True)

    def cleanup(self):
        # This implicitly deletes the temp file
        self.output.close()


commands = sys.argv[1:]
processes = []

for command in commands:
    processes.append(WrappedProcess(command))

for process in processes:
    returncode = process.process.wait()

    with open(process.output.name, 'r') as output:
        shutil.copyfileobj(output, sys.stdout)

    if returncode != 0:
        # FIXME: Terminate the rest of the processes now that this one failed

        sys.exit(returncode)
