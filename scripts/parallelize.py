#!/usr/bin/env python

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
import atexit
import time
import sys


if len(sys.argv) < 2:
    # One is the executable (this script) name, the rest are command lines
    print("ERROR: Need at least one, but suggest at least two command lines to run")
    print()
    print(__doc__)
    sys.exit(1)


class WrappedProcess:
    def __init__(self, commandline):
        self.commandline = commandline

        self.output = tempfile.NamedTemporaryFile()
        atexit.register(self.cleanup)

        # FIXME: Trick wrapped process that it's writing to a terminal. Possible
        # source of inspiration:
        # http://man7.org/tlpi/code/online/dist/pty/unbuffer.c.html

        # FIXME: Set stdin to pipe in from nowhere
        self.process = subprocess.Popen(
            commandline, bufsize=-1, stdout=self.output, stderr=self.output, shell=True)

    def cleanup(self):
        # This implicitly deletes the temp file
        self.output.close()

    def tail_and_wait(self):
        """Like process.wait(), but dumps process output to stdout while waiting"""
        with open(self.output.name, mode='rt') as follow_me:
            while self.process.poll() is None:
                line = follow_me.readline()
                if line:
                    sys.stdout.write(line)
                else:
                    time.sleep(0.5)

            while True:
                # Print the rest of the file if needed
                line = follow_me.readline()
                if not line:
                    break
                sys.stdout.write(line)

        return self.process.returncode


commands = sys.argv[1:]
processes = []

for command in commands:
    processes.append(WrappedProcess(command))

for process in processes:
    returncode = process.tail_and_wait()

    if returncode != 0:
        # Terminate the rest of the processes now that this one failed
        for killme in processes:
            if killme.process.returncode is not None:
                # Already dead
                continue

            print("Terminating remaining process: {}".format(killme.commandline))
            killme.process.terminate()
            killme.process.wait()

        sys.exit(returncode)
