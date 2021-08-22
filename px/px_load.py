"""
Functions for visualizing system load over time in a Unicode graph.

The one you probably want to call is get_load_string().
"""

import os

from . import px_cpuinfo
from . import px_terminal

import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type  # NOQA
    from typing import Tuple  # NOQA


physical, logical = px_cpuinfo.get_core_count()
physical_string = px_terminal.bold(str(physical) + " cores")
cores_string = "[{} | {} virtual]".format(physical_string, logical)


def average_to_level(average, peak):
    level = 3 * (average / peak)
    return int(round(level))


def averages_to_levels(avg0, avg1, avg2):
    """
    Converts three load averages into three levels.

    A level is a 0-3 integer value.

    This function returns the three leves, plus the peak value the levels are
    based on.
    """
    peak = max(avg0, avg1, avg2)
    if peak < 1.0:
        peak = 1.0

    l0 = average_to_level(avg0, peak)
    l1 = average_to_level(avg1, peak)
    l2 = average_to_level(avg2, peak)
    return (l0, l1, l2, peak)


def levels_to_graph(levels):
    """
    Convert an array of levels into a unicode string graph.

    Each level in the levels array is an integer 0-3. Those levels will be
    represented in the graph by 1-4 dots each.

    The returned string will contain two levels per rune.
    """
    if len(levels) % 2 == 1:
        # Left pad uneven-length arrays with an empty column
        levels = [-1] + levels

    # From: http://stackoverflow.com/a/19177754/473672
    unicodify = chr
    try:
        # Python 2
        unicodify = unichr  # type: ignore
    except NameError:
        # Python 3
        pass

    # https://en.wikipedia.org/wiki/Braille_Patterns#Identifying.2C_naming_and_ordering
    LEFT_BAR = [0x00, 0x40, 0x44, 0x46, 0x47]
    RIGHT_BAR = [0x00, 0x80, 0xA0, 0xB0, 0xB8]

    graph = ""
    for index in range(0, len(levels) - 1, 2):
        left_level = levels[index] + 1
        right_level = levels[index + 1] + 1
        code = 0x2800 + LEFT_BAR[left_level] + RIGHT_BAR[right_level]
        graph += unicodify(code)

    return graph


def get_load_values():
    # type: () -> Tuple[float, float, float]
    """
    Returns three system load numbers:
    * The first is the average system load over the last 0m-1m
    * The second is the average system load over the last 1m-5m
    * The third is the average system load over the last 5m-15m
    """
    avg1, avg5, avg15 = os.getloadavg()

    avg0to1 = avg1
    avg1to5 = (5 * avg5 - avg1) / 4.0
    avg5to15 = (15 * avg15 - 5 * avg5) / 10.0

    return (avg0to1, avg1to5, avg5to15)


def get_load_string(load_values=None):
    # type: (Tuple[float, float, float]) -> text_type
    """
    Example return string, underlines indicate bold:
    "1.5  [4 cores | 8 virtual]  [15m load history: GRAPH]"
     ^^^   ^^^^^^^                                  ^^^^^

    Load number is color coded:
    * <= physical core count: Green
    * <= virtual core count: Yellow
    * Larger: Red
    """
    if load_values is None:
        load_values = get_load_values()

    avg0to1, avg1to5, avg5to15 = load_values

    load_string = u"{:.1f}".format(avg0to1)
    if avg0to1 <= physical:
        load_string = px_terminal.green(load_string)
    elif avg0to1 <= logical:
        load_string = px_terminal.yellow(load_string)
    else:
        load_string = px_terminal.red(load_string)

    recent, between, old, peak = averages_to_levels(avg0to1, avg1to5, avg5to15)
    graph = levels_to_graph([old] * 10 + [between] * 4 + [recent])

    # Increase intensity for more recent times
    graph = px_terminal.faint(graph[0:3]) + graph[3:6] + px_terminal.bold(graph[6:])

    return u"{}  {}  [15m load history: {}]".format(load_string, cores_string, graph)
