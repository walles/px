import operator
import subprocess

import os
import re


# Match + group: "47536  1234 root              0:00.03  0.0 /usr/sbin/cupsd -l"
PS_LINE = re.compile(" *([0-9]+) +([0-9]+) +([^ ]+) +([0-9:.]+) +([0-9.]+) +(.*)")

# Match + group: "1:02.03"
CPUTIME_OSX = re.compile("^([0-9]+):([0-9][0-9]\.[0-9]+)$")

# Match + group: "01:23:45"
CPUTIME_LINUX = re.compile("^([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")

# Match + group: "123-01:23:45"
CPUTIME_LINUX_DAYS = re.compile("^([0-9]+)-([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")


class PxProcess(object):
    def __init__(self, process_builder):
        has_cputime = process_builder.cpu_time is not None
        has_memory = process_builder.memory_percent is not None

        self.pid = process_builder.pid
        self.ppid = process_builder.ppid

        self.username = process_builder.username

        self.cpu_time_s = "--"
        if has_cputime:
            self.cpu_time_s = seconds_to_str(process_builder.cpu_time)

        self.memory_percent_s = "--"
        if has_memory:
            self.memory_percent_s = (
                "{:.0f}%".format(process_builder.memory_percent))

        self.cmdline = process_builder.cmdline

        self.score = 0
        if has_memory and has_cputime:
            self.score = (
                (process_builder.cpu_time + 1) *
                (process_builder.memory_percent + 1))

    def __repr__(self):
        # I guess this is really what __str__ should be doing, but the point of
        # implementing this method is to make the py.test output more readable,
        # and py.test calls repr() and not str().
        return str(self.pid) + ":" + self.get_command()

    def match(self, string):
        """
        Returns True if this process matches the string.

        See px_process_test.test_match() for the exact definition of how the
        matching is done.
        """
        if string is None:
            return True

        if self.username == string:
            return True

        if string in self.cmdline:
            return True

        if string in self.cmdline.lower():
            return True

        return False

    def get_command_line_array(self):
        # FIXME: Can we get an actual array from ps? Reverse engineering the
        # array like we do here is bound to be error prone.
        base_split = self.cmdline.split(" ")

        # Try to reverse engineer executables with spaces in their names
        merged_split = list(base_split)
        while not os.path.isfile(merged_split[0]):
            if len(merged_split) == 1:
                # Nothing more to merge, give up
                return base_split

            # Merge the two first elements: http://stackoverflow.com/a/1142879/473672
            merged_split[0:2] = [' '.join(merged_split[0:2])]

        return merged_split

    def get_command(self):
        """Return just the command without any arguments or path"""
        return os.path.basename(self.get_command_line_array()[0])


class PxProcessBuilder(object):
    pass


def call_ps():
    """
    Call ps and return the result in an array of one output line per process
    """
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]
    ps = subprocess.Popen(["ps", "-ax", "-o", "pid,ppid,user,time,%mem,command"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env)
    return ps.communicate()[0].splitlines()[1:]


def parse_time(timestring):
    """Convert a CPU time string returned by ps to a number of seconds"""

    match = CPUTIME_OSX.match(timestring)
    if match:
        minutes = int(match.group(1))
        seconds = float(match.group(2))
        return 60 * minutes + seconds

    match = CPUTIME_LINUX.match(timestring)
    if match:
        hours = int(match.group(1))
        minutes = int(match.group(2))
        seconds = int(match.group(3))
        return 3600 * hours + 60 * minutes + seconds

    match = CPUTIME_LINUX_DAYS.match(timestring)
    if match:
        days = int(match.group(1))
        hours = int(match.group(2))
        minutes = int(match.group(3))
        seconds = int(match.group(4))
        return 86400 * days + 3600 * hours + 60 * minutes + seconds

    raise ValueError("Unparsable timestamp: <" + timestring + ">")


def ps_line_to_process(ps_line):
    match = PS_LINE.match(ps_line)
    assert match is not None

    process_builder = PxProcessBuilder()
    process_builder.pid = int(match.group(1))
    process_builder.ppid = int(match.group(2))
    process_builder.username = match.group(3)
    process_builder.cpu_time = parse_time(match.group(4))
    process_builder.memory_percent = float(match.group(5))
    process_builder.cmdline = match.group(6)

    return PxProcess(process_builder)


def resolve_links(processes):
    """
    On entry, this function assumes that all processes have a "ppid" field
    containing the PID of their parent process.

    When done, all processes will have a "parent" field with a reference to the
    process' parent process object.

    Also, all processes will have a (possibly empty) "children" field containing
    a set of references to child processes.
    """
    pid2process = {}
    for process in processes:
        # Guard against duplicate PIDs
        assert process.pid not in pid2process

        pid2process[process.pid] = process

        process.children = set()

    if 0 not in pid2process:
        # Fake a process 0, this one isn't returned by ps. More info about PID 0:
        # https://en.wikipedia.org/wiki/Process_identifier
        process_builder = PxProcessBuilder()
        process_builder.pid = 0
        process_builder.ppid = None
        process_builder.username = "root"
        process_builder.cpu_time = None
        process_builder.memory_percent = None
        process_builder.cmdline = "kernel PID 0"
        process = PxProcess(process_builder)

        process.children = set()

        processes.append(process)
        pid2process[0] = process

    for process in processes:
        if process.pid == 0:
            process.parent = None
        else:
            process.parent = pid2process[process.ppid]
            process.parent.children.add(process)


def get_all():
    all = map(lambda line: ps_line_to_process(line), call_ps())
    resolve_links(all)
    return all


def order_best_last(processes):
    """Returns process list ordered with the most interesting one last"""
    return sorted(processes, key=operator.attrgetter('score', 'cmdline'))


def seconds_to_str(seconds):
    if seconds < 60:
        seconds_s = str(seconds)
        decimal_index = seconds_s.rfind('.')
        if decimal_index > -1:
            # Chop to at most three decimals
            seconds_s = seconds_s[0:decimal_index + 4]
        return seconds_s + "s"

    if seconds < 3600:
        minutes = int(seconds / 60)
        remaining_seconds = int(seconds - minutes * 60)
        return "{}m{:02d}s".format(minutes, remaining_seconds)

    if seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds - 3600 * hours) / 60)
        return "{}h{:02d}m".format(hours, minutes)

    days = int(seconds / 86400)
    hours = int((seconds - 86400 * days) / 3600)
    return "{}d{:02d}h".format(days, hours)
