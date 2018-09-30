import datetime
import operator
import subprocess

import os
import re
import pwd
import six
import dateutil.tz
from . import px_commandline


import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import Dict        # NOQA
    from typing import MutableSet  # NOQA
    from typing import Text        # NOQA
    from typing import Optional    # NOQA


# Match + group: " 7708 1 Mon Mar  7 09:33:11 2016  netbios 0.1 0:00.08  0.0 /usr/sbin/netbiosd hj"
PS_LINE = re.compile(
    " *([0-9]+) +([0-9]+) +([A-Za-z0-9: ]+) +([^ ]+) +([0-9.]+) +([-0-9.:]+) +([0-9.]+) +(.*)")

# Match + group: "1:02.03"
CPUTIME_OSX = re.compile("^([0-9]+):([0-9][0-9]\.[0-9]+)$")

# Match + group: "01:23:45"
CPUTIME_LINUX = re.compile("^([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")

# Match + group: "123-01:23:45"
CPUTIME_LINUX_DAYS = re.compile("^([0-9]+)-([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")


class PxProcess(object):
    def __init__(self, process_builder, now):
        self.pid = process_builder.pid
        self.ppid = process_builder.ppid

        self.cmdline = process_builder.cmdline
        self.command = self._get_command()
        self.lowercase_command = self.command.lower()

        time = datetime.datetime.strptime(process_builder.start_time_string.strip(), "%c")
        self.start_time = time.replace(tzinfo=dateutil.tz.tzlocal())
        self.age_seconds = (now - self.start_time).total_seconds()
        assert self.age_seconds >= 0
        self.age_s = seconds_to_str(self.age_seconds)

        self.username = process_builder.username

        self.memory_percent = process_builder.memory_percent
        self.memory_percent_s = "--"
        if self.memory_percent is not None:
            self.memory_percent_s = (
                "{:.0f}%".format(process_builder.memory_percent))

        self.cpu_percent = process_builder.cpu_percent
        self.cpu_percent_s = "--"
        if self.cpu_percent is not None:
            self.cpu_percent_s = (
                "{:.0f}%".format(process_builder.cpu_percent))

        # Setting the CPU time like this implicitly recomputes the score
        self.set_cpu_time_seconds(process_builder.cpu_time)

        self.children = None  # type: MutableSet[PxProcess]
        self.parent = None  # type: Optional[PxProcess]

    def __repr__(self):
        # I guess this is really what __str__ should be doing, but the point of
        # implementing this method is to make the py.test output more readable,
        # and py.test calls repr() and not str().
        return str(self.pid) + ":" + self.command

    def __str__(self):
        return self.command + "(" + str(self.pid) + ")"

    def __eq__(self, other):
        if other is None:
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return self.pid

    def _recompute_score(self):
        self.score = 0
        if self.memory_percent is None:
            return
        if self.cpu_time_seconds is None:
            return

        self.score = (
            (self.cpu_time_seconds + 1.0) *
            (self.memory_percent + 1.0) / (self.age_seconds + 1.0))

    def set_cpu_time_seconds(self, seconds):
        self.cpu_time_s = "--"
        self.cpu_time_seconds = None
        if seconds is not None:
            self.cpu_time_s = seconds_to_str(seconds)
            self.cpu_time_seconds = seconds

        self._recompute_score()

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
        return px_commandline.to_array(self.cmdline)

    def _get_command(self):
        """Return just the command without any arguments or path"""
        return px_commandline.get_command(self.cmdline)

    def get_sudo_user(self):
        """Retrieves the $SUDO_USER value for this process, or None if not set"""
        env = os.environ.copy()
        if "LANG" in env:
            del env["LANG"]
        ps = subprocess.Popen(["ps", "e", str(self.pid)],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              env=env)
        stdout = ps.communicate()[0].decode('utf-8')
        match = re.match(".* SUDO_USER=([^ ]+)", stdout, re.DOTALL)
        if not match:
            return None

        return match.group(1)


class PxProcessBuilder(object):
    def __init__(self):
        self.cmdline = None   # type: Text
        self.pid = None       # type: int
        self.ppid = None      # type: Optional[int]
        self.start_time_string = None  # type: Text
        self.username = None  # type: Text
        self.cpu_percent = None  # type: Optional[float]
        self.cpu_time = None  # type: Optional[float]
        self.memory_percent = None  # type: Optional[float]


def call_ps():
    """
    Call ps and return the result in an iterable of one output line per process
    """
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]
    ps = subprocess.Popen(["ps", "-ax", "-o", "pid,ppid,lstart,uid,pcpu,time,%mem,command"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=env)
    return ps.communicate()[0].decode('utf-8').splitlines()[1:]


def parse_time(timestring):
    # type: (str) -> float
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


def uid_to_username(uid):
    # type: (int)->Text
    try:
        return six.text_type(pwd.getpwuid(uid).pw_name)
    except KeyError:
        return six.text_type(uid)


def ps_line_to_process(ps_line, now):
    match = PS_LINE.match(ps_line)
    assert match is not None

    process_builder = PxProcessBuilder()
    process_builder.pid = int(match.group(1))
    process_builder.ppid = int(match.group(2))
    process_builder.start_time_string = match.group(3)
    process_builder.username = uid_to_username(int(match.group(4)))
    process_builder.cpu_percent = float(match.group(5))
    process_builder.cpu_time = parse_time(match.group(6))
    process_builder.memory_percent = float(match.group(7))
    process_builder.cmdline = match.group(8)

    return PxProcess(process_builder, now)


def create_kernel_process(now):
    # Fake a process 0, this one isn't returned by ps. More info about PID 0:
    # https://en.wikipedia.org/wiki/Process_identifier
    process_builder = PxProcessBuilder()
    process_builder.pid = 0
    process_builder.ppid = None

    # FIXME: This should be the system boot timestamp, not the epoch
    process_builder.start_time_string = datetime.datetime.utcfromtimestamp(0).strftime("%c")

    process_builder.username = u"root"
    process_builder.cpu_time = None
    process_builder.memory_percent = None
    process_builder.cmdline = u"kernel PID 0"
    process = PxProcess(process_builder, now)

    process.children = set()

    return process


def resolve_links(processes, now):
    # type: (Dict[int, PxProcess], datetime.datetime) -> None
    """
    On entry, this function assumes that all processes have a "ppid" field
    containing the PID of their parent process.

    When done, all processes will have a "parent" field with a reference to the
    process' parent process object.

    Also, all processes will have a (possibly empty) "children" field containing
    a set of references to child processes.
    """
    for process in processes.values():
        process.children = set()

    if 0 not in processes:
        kernel_process = create_kernel_process(now)
        processes[0] = kernel_process

    for process in processes.values():
        if process.pid == 0:
            process.parent = None
        else:
            process.parent = processes[process.ppid]
            process.parent.children.add(process)


def remove_process_and_descendants(processes, pid):
    process = processes[pid]
    process.parent.children.remove(process)
    toexclude = [process]
    while toexclude:
        process = toexclude.pop()
        del processes[process.pid]
        for child in process.children:
            toexclude.append(child)


def get_all():
    processes = {}
    ps_lines = call_ps()
    now = datetime.datetime.now().replace(tzinfo=dateutil.tz.tzlocal())
    for ps_line in ps_lines:
        process = ps_line_to_process(ps_line, now)
        processes[process.pid] = process

    resolve_links(processes, now)
    remove_process_and_descendants(processes, os.getpid())

    return processes.values()


def order_best_last(processes):
    """Returns process list ordered with the most interesting one last"""
    return sorted(processes, key=operator.attrgetter('score', 'cmdline'))


def order_best_first(processes):
    """Returns process list ordered with the most interesting one first"""
    ordered = sorted(processes, key=operator.attrgetter('cmdline'))
    ordered = sorted(ordered, key=operator.attrgetter('score'), reverse=True)
    return ordered


def seconds_to_str(seconds):
    if seconds < 60:
        seconds_s = str(seconds)
        decimal_index = seconds_s.rfind('.')
        if decimal_index > -1:
            # Chop to at most two decimals
            seconds_s = seconds_s[0:decimal_index + 3]
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
