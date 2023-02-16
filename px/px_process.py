import logging
import datetime
import operator

import os
import re
import pwd
import errno
import subprocess
import dateutil.tz

from . import px_commandline
from . import px_exec_util


from typing import Dict
from typing import MutableSet
from typing import Optional
from typing import List
from typing import Iterable


LOG = logging.getLogger(__name__)


# Match + group: " 7708 1 Mon Mar  7 09:33:11 2016  netbios 0.1 0:00.08  0.0 /usr/sbin/netbiosd hj"
PS_LINE = re.compile(
    " *([0-9]+) +([0-9]+) +([0-9]+) +([A-Za-z0-9: ]+) +([^ ]+) +([0-9.]+) +([-0-9.:]+) +([0-9.]+) +(.*)"
)

# Match + group: "1:02.03"
CPUTIME_OSX = re.compile(r"^([0-9]+):([0-9][0-9]\.[0-9]+)$")

# Match + group: "01:23:45"
CPUTIME_LINUX = re.compile("^([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")

# Match + group: "123-01:23:45"
CPUTIME_LINUX_DAYS = re.compile("^([0-9]+)-([0-9][0-9]):([0-9][0-9]):([0-9][0-9])$")


TIMEZONE = dateutil.tz.tzlocal()


uid_to_username_cache: Dict[int, str] = {}
get_command_cache: Dict[str, str] = {}


def _parse_time(time_s: str) -> datetime.datetime:
    """
    Parse a local date from ps into a datetime.datetime object.

    Example inputs:
      "Wed Dec 16 12:41:43 2020"
      "Sat Jan  9 14:20:34 2021"
    """

    zero_based_month = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ].index(time_s[4:7])

    day_of_month = int(time_s[8:10])
    hour = int(time_s[11:13])
    minute = int(time_s[14:16])
    second = int(time_s[17:19])
    year = int(time_s[20:24])

    return datetime.datetime(
        year, zero_based_month + 1, day_of_month, hour, minute, second, tzinfo=TIMEZONE
    )


class PxProcess:
    # pylint: disable=attribute-defined-outside-init
    def __init__(
        self,
        cmdline: str,
        pid: int,
        rss_kb: int,
        start_time_string: str,
        username: str,
        now: datetime.datetime,
        ppid: Optional[int],
        memory_percent: Optional[float] = None,
        cpu_percent: Optional[float] = None,
        cpu_time: Optional[float] = None,
    ) -> None:
        self.pid: int = pid
        self.ppid: Optional[int] = ppid
        self.rss_kb: int = rss_kb

        self.cmdline: str = cmdline
        self.command: str = self._get_command()
        self.lowercase_command: str = self.command.lower()

        self.start_time = _parse_time(start_time_string.strip())
        self.age_seconds: float = (now - self.start_time).total_seconds()
        if self.age_seconds < -10:
            # See: https://github.com/walles/px/issues/84
            #
            # We used to check for negative age, but since we look at the clock
            # once to begin with, and then spend some milliseconds calling ps,
            # we can sometimes find new processes with a timestamp that is newer
            # than "now".
            #
            # If this is the cause, we should be well below 10s, since process
            # listing doesn't take that long.
            #
            # If it takes more than 10s, something else is likely up.
            LOG.error(
                "Process age < -10: age_seconds=%r now=%r start_time=%r start_time_string=%r timezone=%r",
                self.age_seconds,
                now,
                self.start_time,
                start_time_string.strip(),
                datetime.datetime.now(TIMEZONE).tzname(),
            )
            assert False
        if self.age_seconds < 0:
            self.age_seconds = 0

        self.age_s: str = seconds_to_str(self.age_seconds)

        self.username: str = username

        self.memory_percent = memory_percent
        self.memory_percent_s: str = "--"
        if memory_percent is not None:
            self.memory_percent_s = f"{memory_percent:.0f}%"

        self.cpu_percent = cpu_percent
        self.cpu_percent_s: str = "--"
        if cpu_percent is not None:
            self.cpu_percent_s = f"{cpu_percent:.0f}%"

        # Setting the CPU time like this implicitly recomputes the score
        self.set_cpu_time_seconds(cpu_time)

        self.children: MutableSet[PxProcess] = set()
        self.parent: Optional[PxProcess] = None

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
        self.score = 0.0
        if self.memory_percent is None:
            return
        if self.cpu_time_seconds is None:
            return

        self.score = (
            (self.cpu_time_seconds + 1.0)
            * (self.memory_percent + 1.0)
            / (self.age_seconds + 1.0)
        )

    def set_cpu_time_seconds(self, seconds: Optional[float]) -> None:
        self.cpu_time_s: str = "--"
        self.cpu_time_seconds = None
        if seconds is not None:
            self.cpu_time_s = seconds_to_str(seconds)
            self.cpu_time_seconds = seconds

        self._recompute_score()

    def match(self, string, require_exact_user=True):
        """
        Returns True if this process matches the string.

        See px_process_test.test_match() for the exact definition of how the
        matching is done.
        """
        if string is None:
            return True

        if self.username == string:
            return True

        if not require_exact_user:
            if self.username.startswith(string):
                return True

        if string in self.cmdline:
            return True

        if string in self.cmdline.lower():
            return True

        if str(self.pid).startswith(string):
            return True

        return False

    def get_command_line_array(self):
        return px_commandline.to_array(self.cmdline)

    def _get_command(self):
        """Return just the command without any arguments or path"""
        if self.cmdline in get_command_cache:
            return get_command_cache[self.cmdline]

        command = px_commandline.get_command(self.cmdline)
        get_command_cache[self.cmdline] = command

        return command

    def get_sudo_user(self):
        """Retrieves the $SUDO_USER value for this process, or None if not set"""
        stdout = px_exec_util.run(["ps", "e", str(self.pid)])
        match = re.match(".* SUDO_USER=([^ ]+)", stdout, re.DOTALL)
        if not match:
            return None

        return match.group(1)

    def is_alive(self):
        try:
            # Signal 0 has no effect
            os.kill(self.pid, 0)
        except OSError as e:
            if e.errno == errno.ESRCH:
                # No such process
                return False

            # Process found but something else went wrong
            return True

        # No problem, process was there
        return True


class PxProcessBuilder:
    def __init__(self):
        self.cmdline: Optional[str] = None
        self.pid: Optional[int] = None
        self.ppid: Optional[int] = None
        self.rss_kb: Optional[int] = None
        self.start_time_string: Optional[str] = None
        self.username: Optional[str] = None
        self.cpu_percent: Optional[float] = None
        self.cpu_time: Optional[float] = None
        self.memory_percent: Optional[float] = None

    def __repr__(self):
        # pylint: disable=consider-using-f-string
        return (
            "start_time_string=%r pid=%r ppid=%r user=%r cpu%%=%r cputime=%r mem%%=%r cmd=<%r>"
            % (
                self.start_time_string,
                self.pid,
                self.ppid,
                self.username,
                self.cpu_percent,
                self.cpu_time,
                self.memory_percent,
                self.cmdline,
            )
        )

    def build(self, now: datetime.datetime) -> PxProcess:
        assert self.cmdline
        assert self.pid is not None
        assert self.rss_kb is not None
        assert self.start_time_string
        assert self.username
        return PxProcess(
            cmdline=self.cmdline,
            pid=self.pid,
            ppid=self.ppid,
            rss_kb=self.rss_kb,
            start_time_string=self.start_time_string,
            username=self.username,
            now=now,
            memory_percent=self.memory_percent,
            cpu_percent=self.cpu_percent,
            cpu_time=self.cpu_time,
        )


def parse_time(timestring: str) -> float:
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


def uid_to_username(uid: int) -> str:
    if uid in uid_to_username_cache:
        return uid_to_username_cache[uid]

    # Populate cache
    try:
        uid_to_username_cache[uid] = str(pwd.getpwuid(uid).pw_name)
    except KeyError:
        uid_to_username_cache[uid] = str(uid)

    return uid_to_username_cache[uid]


def ps_line_to_process(ps_line: str, now: datetime.datetime) -> PxProcess:
    match = PS_LINE.match(ps_line)
    if not match:
        raise Exception(f"Failed to match ps line <{ps_line:!r}>")

    process_builder = PxProcessBuilder()
    process_builder.pid = int(match.group(1))
    process_builder.ppid = int(match.group(2))
    process_builder.rss_kb = int(match.group(3))
    process_builder.start_time_string = match.group(4)
    process_builder.username = uid_to_username(int(match.group(5)))
    process_builder.cpu_percent = float(match.group(6))
    process_builder.cpu_time = parse_time(match.group(7))
    process_builder.memory_percent = float(match.group(8))
    process_builder.cmdline = match.group(9)

    return process_builder.build(now)


def create_kernel_process(now: datetime.datetime) -> PxProcess:
    """
    Fake a process 0, this one isn't returned by ps. More info about PID 0:
    https://en.wikipedia.org/wiki/Process_identifier
    """
    process_builder = PxProcessBuilder()
    process_builder.pid = 0
    process_builder.ppid = None

    # FIXME: This should be the system boot timestamp, not the epoch
    process_builder.start_time_string = datetime.datetime.utcfromtimestamp(0).strftime(
        "%c"
    )

    process_builder.rss_kb = 0
    process_builder.username = "root"
    process_builder.cpu_time = None
    process_builder.memory_percent = None
    process_builder.cmdline = "kernel PID 0"
    process = process_builder.build(now)

    return process


def resolve_links(processes: Dict[int, PxProcess], now: datetime.datetime) -> None:
    """
    On entry, this function assumes that all processes have a "ppid" field
    containing the PID of their parent process.

    When done, all processes will have a "parent" field with a reference to the
    process' parent process object.

    Also, all processes will have a (possibly empty) "children" field containing
    a set of references to child processes.
    """
    if 0 not in processes:
        kernel_process = create_kernel_process(now)
        processes[0] = kernel_process

    for process in processes.values():
        if process.pid == 0:
            process.parent = None
        elif process.ppid is None:
            process.parent = None
        else:
            process.parent = processes.get(process.ppid)

        if process.parent is not None:
            process.parent.children.add(process)


def remove_process_and_descendants(processes: Dict[int, PxProcess], pid: int) -> None:
    process = processes[pid]
    if process.parent is not None:
        process.parent.children.remove(process)
    toexclude = [process]
    while toexclude:
        process = toexclude.pop()
        del processes[process.pid]
        for child in process.children:
            toexclude.append(child)


def get_all() -> List[PxProcess]:
    processes = {}

    # NOTE: Both the full path to ps and "close_fds = False" are important
    # because they enable the use of _posix_spawn()...
    #
    # https://github.com/python/cpython/blob/998ae1fa3fb05a790071217cf8f6ae3a928da13f/Lib/subprocess.py#L1715
    #
    # ... and avoids prematurely waiting for ps to produce 50000 bytes:
    #
    # https://github.com/python/cpython/blob/998ae1fa3fb05a790071217cf8f6ae3a928da13f/Lib/subprocess.py#L1796
    #
    # If you want to change this, try benchmark_proc_get_all.py and make sure
    # you don't regress.
    close_fds = False
    command = [
        "/bin/ps",
        "-ax",
        "-o",
        "pid=,ppid=,rss=,lstart=,uid=,pcpu=,time=,%mem=,command=",
    ]

    with open(os.devnull, "w", encoding="utf-8") as DEVNULL:
        with subprocess.Popen(
            command,
            stdin=DEVNULL,
            stdout=subprocess.PIPE,
            stderr=DEVNULL,
            close_fds=close_fds,
            env=px_exec_util.ENV,
        ) as ps:

            stdout = ps.stdout
            assert stdout
            now = datetime.datetime.now().replace(tzinfo=TIMEZONE)
            for ps_line in stdout:
                process = ps_line_to_process(ps_line.decode("utf-8"), now)
                processes[process.pid] = process

            if ps.wait() != 0:
                raise OSError(f"Exit code {ps.returncode} from {command}")

    resolve_links(processes, now)
    remove_process_and_descendants(processes, os.getpid())

    return list(processes.values())


def order_best_last(processes: Iterable[PxProcess]) -> List[PxProcess]:
    """Returns process list ordered with the most interesting one last"""
    return sorted(processes, key=operator.attrgetter("score", "cmdline"))


def order_best_first(processes: Iterable[PxProcess]) -> List[PxProcess]:
    """Returns process list ordered with the most interesting one first"""
    ordered = sorted(processes, key=operator.attrgetter("cmdline"))
    ordered = sorted(ordered, key=operator.attrgetter("score"), reverse=True)
    return ordered


def seconds_to_str(seconds: float) -> str:
    if seconds < 60:
        seconds_s = str(seconds)
        decimal_index = seconds_s.rfind(".")
        if decimal_index > -1:
            # Chop to at most two decimals
            seconds_s = seconds_s[0 : decimal_index + 3]
        return seconds_s + "s"

    if seconds < 3600:
        minutes = int(seconds / 60)
        remaining_seconds = int(seconds - minutes * 60)
        return f"{minutes}m{remaining_seconds:02d}s"

    if seconds < 86400:
        hours = int(seconds / 3600)
        minutes = int((seconds - 3600 * hours) / 60)
        return f"{hours}h{minutes:02d}m"

    days = int(seconds / 86400)
    hours = int((seconds - 86400 * days) / 3600)
    return f"{days}d{hours:02d}h"
