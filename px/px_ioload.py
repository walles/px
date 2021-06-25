"""
Functions for visualizing where IO is bottlenecking.
"""

import datetime
import math
import six
import re

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
NETSTAT_IB_LINE_RE = re.compile(r"^([^ ]+).*[0-9]+ +([0-9]+) +[0-9]+ +[0-9]+ +([0-9]+) +[0-9]+$")

def parse_netstat_ib_output(netstat_ib_output):
    # type: (six.text_type) -> List[Sample]
    samples = []  # type: List[Sample]
    for line in netstat_ib_output.splitlines()[1:]:
        match = NETSTAT_IB_LINE_RE.match(line)
        if not match:
            continue

        incoming_bytes = int(match[2])
        outgoing_bytes = int(match[3])
        if incoming_bytes == 0 and outgoing_bytes == 0:
            # For our purposes this is just clutter
            continue

        samples.append(Sample(match[1] + " incoming", incoming_bytes))
        samples.append(Sample(match[1] + " outgoing", outgoing_bytes))

    return samples


class Sample(object):
    def __init__(self, name, bytecount):
        # type: (six.text_type, int) -> None
        self.name = name
        self.bytecount = bytecount

    def __repr__(self) -> str:
        return 'Sample[name="{}", count={}]'.format(self.name, self.bytecount)

    def __eq__(self, o):
        return self.bytecount == o.bytecount and self.name == o.name


class SystemState(object):
    def __init__(self):
        # type: () -> None
        self.timestamp = datetime.datetime.now()

        # FIXME: Populate this list from the current system
        self.samples = self.sample_network_interfaces()  # type: List[Sample]

    def sample_network_interfaces(self):
        # type: () -> List[Sample]
        samples = []  # type: List[Sample]

        # Append network interfaces byte counts
        # FIXME: This is macOS specific
        netstat_ib_output = px_exec_util.run(["netstat", '-ib'])
        samples += parse_netstat_ib_output(netstat_ib_output)

        # FIXME: Append hard drives / whatever drives byte counts

        return samples


class PxIoLoad(object):
    def __init__(self):
        # type: () -> None
        self.most_recent_system_state = SystemState()  # type: SystemState
        self.previous_system_state = None  # type: Optional[SystemState]

        # Maps a subsystem name ("eth0 outgoing") to a current bytes-per-second
        # value and a high watermark for the same value.
        self.ios = {}  # type: Dict[six.text_type, Tuple[float, float]]

    def update(self):
        # type: () -> None

        since_last_update = datetime.datetime.now() - self.most_recent_system_state.timestamp
        if since_last_update.total_seconds() < 0.5:
            # If we sample too close together the differences will be too unreliable
            return

        self.previous_system_state = self.most_recent_system_state
        self.most_recent_system_state = SystemState()

        # FIXME: Update self.ios from the system states

    def get_load_string(self):
        """
        Example return value: "14%  [123B/s / 878B/s] eth0 outgoing"
        """

        # NOTE: To compute this value, we need a collection of data points, with
        # each data point containing:
        # * A name ("eth0 outgoing")
        # * A current bytes-per-second value (42.1)
        # * The high watermark value
        #
        # This data is available in self.ios.
        #
        # Then, we need to sort these by percentages, and render the top one.

        if not self.ios:
            # No load collected
            return "..."

        # Values per entry: name, percentage, current value, high watermark
        collected_ios = []  # type: List[Tuple[six.text_type, int, float, float]]
        for name, loads in six.iteritems(self.ios):
            percentage = 0  # type: int
            if loads[1] > 0:
                percentage = math.trunc((100 * loads[0]) / loads[1])

            collected_ios.append((name, percentage, loads[0], loads[1]))

        # Highest percentage first
        collected_ios.sort(key=lambda collectee: collectee[1], reverse=True)

        bottleneck = collected_ios[0]

        # "14%  [123B/s / 878B/s] eth0 outgoing"
        # FIXME: At least the percentage should be in white, make this look nice
        return "{:3s}%  [{}B/s / {}B/s] {}".format(
            bottleneck[1],
            math.trunc(bottleneck[2]),
            math.trunc(bottleneck[3]),
            bottleneck[0]
        )

_ioload = PxIoLoad()


def update():
    _ioload.update()


def get_load_string():
    return _ioload.get_load_string()
