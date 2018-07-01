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
        # FIXME: Remove the tempfile before exiting
        self.output = tempfile.NamedTemporaryFile()

        # FIXME: Trick wrapped process that it's writing to a terminal. Possible
        # source of inspiration:
        # http://man7.org/tlpi/code/online/dist/pty/unbuffer.c.html

        # FIXME: Set stdin to pipe in from nowhere
        self.process = subprocess.Popen(
            cmdline, bufsize=-1, stdout=self.output, stderr=self.output, shell=True)


commands = sys.argv[1:]
processes = []

for command in commands:
    processes.append(WrappedProcess(command))

for process in processes:
    process.process.wait()

    with open(process.output.name, 'r') as output:
        shutil.copyfileobj(output, sys.stdout)

    # FIXME: Terminate the rest of the processes if this one failed

    # FIXME: Exit with this process' exit code if it failed

# FIXME: Clean up the tempfiles
