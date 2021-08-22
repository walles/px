"""
Functions for visualizing where IO is bottlenecking.
"""

import datetime
import math
import six
import re
import os

from . import px_units
from . import px_terminal
from . import px_exec_util

import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List
    from typing import Dict
    from typing import Tuple
    from typing import Optional


# Matches output lines in "netstat -ib" on macOS.
#
# Extracted columns are interface name, incoming bytes count and outgoing bytes
# count.
#
# If you look carefully at the output, this regex will only match lines with
# error counts, which is only one line per interface.
NETSTAT_IB_LINE_RE = re.compile(
    r"^([^ ]+).*[0-9]+ +([0-9]+) +[0-9]+ +[0-9]+ +([0-9]+) +[0-9]+$"
)

# Parse a line from /proc/net/dev.
#
# Example input (includes leading whitespace):
#   eth0: 29819439   19890    0    0    0     0          0         0   364327    6584    0    0    0     0       0          0
PROC_NET_DEV_RE = re.compile(
    r"^ *([^:]+): +([0-9]+) +[0-9]+ +[0-9]+ +[0-9]+ +[0-9]+ +[0-9]+ +[0-9]+ +[0-9]+ +([0-9]+)[0-9 ]+$"
)

# Parse a line from /proc/diskstats
#
# First group is the name. To get partitions rather than disks we require the
# name to end in a number.
#
# Second and third groups are sector reads and writes respectively.
#
# Line format documented here:
# https://www.kernel.org/doc/Documentation/admin-guide/iostats.rst
PROC_DISKSTATS_RE = re.compile(
    r"^ *[0-9]+ +[0-9]+ ([a-z]+[0-9]+) [0-9]+ [0-9]+ ([0-9]+) [0-9]+ [0-9]+ [0-9]+ ([0-9]+) .*"
)


def parse_netstat_ib_output(netstat_ib_output):
    # type: (six.text_type) -> List[Sample]
    """
    Parse output of "netstat -ib" on macOS.
    """
    samples = []  # type: List[Sample]
    for line in netstat_ib_output.splitlines()[1:]:
        match = NETSTAT_IB_LINE_RE.match(line)
        if not match:
            continue

        incoming_bytes = int(match.group(2))
        outgoing_bytes = int(match.group(3))
        if incoming_bytes == 0 and outgoing_bytes == 0:
            # For our purposes this is just clutter
            continue

        samples.append(Sample(match.group(1) + " incoming", incoming_bytes))
        samples.append(Sample(match.group(1) + " outgoing", outgoing_bytes))

    return samples


def parse_iostat_output(iostat_output):
    # type: (six.text_type) -> List[Sample]
    """
    Parse output of "iostat -dKI -n 99" on macOS.
    """
    lines = iostat_output.splitlines()

    # Example: ["disk0"]
    names = lines[0].split()

    # Example: ["15.95", "2816998", "43889.27"]
    #
    # Numbers are: "KB/t", "xfrs" and "xfrs"
    numbers = lines[2].split()

    samples = []  # type: List[Sample]
    for i in range(len(names)):
        name = names[i]
        mb_string = numbers[3 * i + 2]

        # 1024 * 1024 mirrors what happens in iostat.c:
        # https://opensource.apple.com/source/system_cmds/system_cmds-550.6/iostat.tproj/iostat.c.auto.html
        bytecount = math.trunc(float(mb_string) * 1024 * 1024)

        samples.append(Sample(name, bytecount))

    return samples


def parse_proc_net_dev(proc_net_dev_contents):
    # type: (six.text_type) -> List[Sample]
    """
    Parse /proc/net/dev contents into a list of samples.
    """
    return_me = []  # type: List[Sample]
    for line in proc_net_dev_contents.splitlines():
        match = PROC_NET_DEV_RE.match(line)
        if not match:
            continue

        name = match.group(1)
        incoming = int(match.group(2))
        outgoing = int(match.group(3))
        if incoming == 0 and outgoing == 0:
            continue

        return_me.append(Sample(name + " incoming", incoming))
        return_me.append(Sample(name + " outgoing", outgoing))

    return return_me


def parse_proc_diskstats(proc_diskstats_contents):
    # type: (six.text_type) -> List[Sample]
    """
    Parse /proc/net/dev contents into a list of samples.
    """
    return_me = []  # type: List[Sample]
    for line in proc_diskstats_contents.splitlines():
        match = PROC_DISKSTATS_RE.match(line)
        if not match:
            continue

        name = match.group(1)
        read_sectors = int(match.group(2))
        write_sectors = int(match.group(3))
        if read_sectors == 0 and write_sectors == 0:
            continue

        # Multiply by 512 to get bytes from sectors:
        # https://stackoverflow.com/a/38136179/473672
        return_me.append(Sample(name + " read", read_sectors * 512))
        return_me.append(Sample(name + " write", write_sectors * 512))

    return return_me


class Sample(object):
    def __init__(self, name, bytecount):
        # type: (six.text_type, int) -> None
        self.name = name
        self.bytecount = bytecount

    def __repr__(self):
        return 'Sample[name="{}", count={}]'.format(self.name, self.bytecount)

    def __eq__(self, o):
        return self.bytecount == o.bytecount and self.name == o.name


class SubsystemStat(object):
    def __init__(self, throughput, high_watermark):
        # type: (float, float) -> None

        if throughput > high_watermark:
            raise ValueError(
                "High watermark {} lower than throughput {}".format(
                    high_watermark, throughput
                )
            )

        self.throughput = throughput
        self.high_watermark = high_watermark


class SystemState(object):
    def __init__(self):
        # type: () -> None
        self.timestamp = datetime.datetime.now()

        self.samples = (
            self.sample_network_interfaces() + self.sample_drives()
        )  # type: List[Sample]

        by_name = {}  # type: Dict[six.text_type, Sample]
        for sample in self.samples:
            by_name[sample.name] = sample
        self.samples_by_name = by_name

    def sample_network_interfaces(self):
        # type: () -> List[Sample]
        """
        Query system for network interfaces byte counts
        """

        if os.path.exists("/proc/net/dev"):
            # We're on Linux
            with open("/proc/net/dev") as proc_net_dev:
                return parse_proc_net_dev(proc_net_dev.read())

        # Assuming macOS, add support for more platforms on demand
        netstat_ib_output = px_exec_util.run(["netstat", "-ib"])
        return parse_netstat_ib_output(netstat_ib_output)

    def sample_drives(self):
        # type: () -> List[Sample]
        """
        Query system for drive statistics
        """

        if os.path.exists("/proc/diskstats"):
            # We're on Linux
            with open("/proc/diskstats") as proc_diskstats:
                return parse_proc_diskstats(proc_diskstats.read())

        # Assuming macOS, add support for more platforms on demand
        iostat_output = px_exec_util.run(["iostat", "-dKI", "-n 99"])
        return parse_iostat_output(iostat_output)


class PxIoLoad(object):
    def __init__(self):
        # type: () -> None
        self.most_recent_system_state = SystemState()  # type: SystemState
        self.previous_system_state = None  # type: Optional[SystemState]

        # Maps a subsystem name ("eth0 outgoing") to a current bytes-per-second
        # value and a high watermark for the same value.
        self.ios = {}  # type: Dict[six.text_type, SubsystemStat]

        # Per interface, keep track of when we first saw it and its byte count
        # at that time.
        self.baseline = {}  # type: Dict[six.text_type, Tuple[datetime.datetime, int]]
        self.update_baseline_from_system(self.most_recent_system_state)

    def update_baseline_from_system(self, system_state):
        # type: (SystemState) -> None
        """
        Add new entries to the baseline, and remove those that aren't part of
        the system state any more.
        """
        unseen = set(self.baseline.keys())
        now = system_state.timestamp
        for sample in system_state.samples:
            if sample.name in unseen:
                unseen.remove(sample.name)

            if sample.name in self.baseline:
                # Already in there, move along!
                continue

            self.baseline[sample.name] = (now, sample.bytecount)

        # Garbage collect removed devices
        for remove_me in unseen:
            del self.baseline[remove_me]

    def update(self):
        # type: () -> None

        self.previous_system_state = self.most_recent_system_state
        self.most_recent_system_state = SystemState()
        self.update_baseline_from_system(self.most_recent_system_state)

        seconds_since_previous = (
            self.most_recent_system_state.timestamp
            - self.previous_system_state.timestamp
        ).total_seconds()
        assert seconds_since_previous > 0

        # Update self.ios from the system states
        updated_ios = {}  # type: Dict[six.text_type, SubsystemStat]
        for sample in self.most_recent_system_state.samples:
            name = sample.name

            baseline_sample = self.baseline[name]
            bytes_since_baseline = sample.bytecount - baseline_sample[1]
            assert bytes_since_baseline >= 0
            seconds_since_baseline = (
                self.most_recent_system_state.timestamp - baseline_sample[0]
            ).total_seconds()
            if seconds_since_baseline == 0:
                # Newly added device, need two samples to make a metric, try
                # again next time
                continue

            previous_sample = self.previous_system_state.samples_by_name.get(name)
            if not previous_sample:
                # Need two samples to make a metric
                continue
            bytes_since_previous = sample.bytecount - previous_sample.bytecount
            assert bytes_since_previous >= 0

            assert bytes_since_baseline >= bytes_since_previous

            bytes_per_second_since_baseline = (
                bytes_since_baseline / seconds_since_baseline
            )
            bytes_per_second_since_previous = (
                bytes_since_previous / seconds_since_previous
            )

            io_entry = self.ios.get(name)
            if not io_entry:
                # New device
                io_entry = SubsystemStat(throughput=0.0, high_watermark=0.0)

            # High watermark throughput should be measured vs the last sample...
            high_watermark = max(
                io_entry.high_watermark, bytes_per_second_since_previous
            )
            assert high_watermark >= bytes_per_second_since_baseline

            # ... but the current B/s should be measured vs the initial sample.
            # This makes the values more stable and easier on the eye.
            updated_ios[name] = SubsystemStat(
                throughput=bytes_per_second_since_baseline,
                high_watermark=high_watermark,
            )

        self.ios = updated_ios

    def get_load_string(self):
        # type: () -> six.text_type
        """
        Example return value: "[123B/s / 878B/s] eth0 outgoing"
        """

        # NOTE: To compute this value, we need a collection of data points, with
        # each data point containing:
        # * A name ("eth0 outgoing")
        # * A current bytes-per-second value (42.1)
        # * The high watermark value
        #
        # This data is available in self.ios.
        #
        # Then, we need to sort these by current-bytes-per-second, and render the top one.

        # Values per entry: name, current value, high watermark
        collected_ios = []  # type: List[Tuple[six.text_type, float, float]]
        for name, loads in six.iteritems(self.ios):
            collected_ios.append((name, loads.throughput, loads.high_watermark))

        if not collected_ios:
            # No load collected
            return ""

        # Highest throughput first
        collected_ios.sort(key=lambda collectee: collectee[1], reverse=True)

        bottleneck = collected_ios[0]
        return "[{} / {}] {}".format(
            px_terminal.bold(
                px_units.bytes_to_string(math.trunc(bottleneck[1])) + "/s"
            ),
            px_units.bytes_to_string(math.trunc(bottleneck[2])) + "/s",
            px_terminal.bold(bottleneck[0]),
        )


_ioload = PxIoLoad()


def update():
    _ioload.update()


def get_load_string():
    return _ioload.get_load_string()
