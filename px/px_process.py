import subprocess

import os
import re


# Match + group: "47536 root              0:00.03  0.0 /usr/sbin/cupsd -l"
PS_LINE = re.compile(" *([0-9]+) +([^ ]+) +([0-9:.]+) +([0-9.]+) +(.*)")


class PxProcess(object):
    def __init__(self, process_builder):
        self.pid = process_builder.pid

        self.username = process_builder.username

        self.cpu_time_s = "{:.3f}s".format(process_builder.cpu_time)

        self.memory_percent_s = (
            "{:.0f}%".format(process_builder.memory_percent))

        self.cmdline = process_builder.cmdline

        self.score = (
            (process_builder.cpu_time + 1) *
            (process_builder.memory_percent + 1))


class PxProcessBuilder(object):
    pass


def call_ps():
    """
    Call ps and return the result in an array of one output line per process
    """
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]
    ps = subprocess.Popen(["ps", "-ax", "-o", "pid,user,time,%mem,command"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env)
    return ps.communicate()[0].splitlines()[1:]


def parse_time(timestring):
    """Convert a CPU time string returned by ps to a number of seconds"""
    return 5


def ps_line_to_process(ps_line):
    match = PS_LINE.match(ps_line)
    assert match is not None

    process_builder = PxProcessBuilder()
    process_builder.pid = int(match.group(1))
    process_builder.username = match.group(2)
    process_builder.cpu_time = parse_time(match.group(3))
    process_builder.memory_percent = float(match.group(4))
    process_builder.cmdline = match.group(5)

    return PxProcess(process_builder)


def get_all():
    return map(lambda line: ps_line_to_process(line), call_ps())
