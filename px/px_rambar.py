import sys
import operator

from px import px_terminal

from . import px_process

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List  # NOQA
    from typing import Dict  # NOQA
    from typing import Tuple  # NOQA
    from six import text_type  # NOQA

GROUPS_COUNT = 4


def get_categories(all_processes):
    # type: (List[px_process.PxProcess]) -> List[Tuple[text_type, int]]
    """
    Group processes by pretty names, keeping track of the total rss_kb in each
    group.

    Return the top groups in order plus one "other" which is the sum of the
    rest. The total number of returned groups will be GROUPS_COUNT.
    """

    names_to_kilobytes = {}  # type: Dict[text_type, int]
    for process in all_processes:
        base_kb = 0
        if process.command in names_to_kilobytes:
            base_kb = names_to_kilobytes[process.command]
        else:
            base_kb = 0

        names_to_kilobytes[process.command] = base_kb + process.rss_kb

    sorted_names = sorted(
        names_to_kilobytes.items(), key=operator.itemgetter(1), reverse=True
    )
    other_total_kb = 0
    return_me = []  # type: List[Tuple[text_type, int]]
    for i, name_and_kilobytes in enumerate(sorted_names):
        if i < GROUPS_COUNT - 1:
            return_me.append(name_and_kilobytes)
        else:
            other_total_kb += name_and_kilobytes[1]
    return_me.append(("...", other_total_kb))

    return return_me


def rambar(ram_bar_length, all_processes):
    # type: (int, List[px_process.PxProcess]) -> text_type

    categories = get_categories(all_processes)
    total_kilobytes = 0
    for category in categories:
        total_kilobytes += category[1]

    bar = u""
    for i, category in enumerate(categories):
        name = category[0]
        kilobytes = category[1]

        chars = int(round(ram_bar_length * kilobytes * 1.0 / total_kilobytes))
        if i == len(categories) - 1:
            # Use all remaining chars
            chars = ram_bar_length - px_terminal.visual_length(bar)

        add_to_bar = px_terminal.get_string_of_length(" " + name, chars)
        if i == 0:
            # First red
            add_to_bar = px_terminal.red(add_to_bar)
        elif i == 1:
            # Second yellow
            add_to_bar = px_terminal.yellow(add_to_bar)
        elif i % 2 == 1:
            # Then alternating between normal and inverse video
            add_to_bar = px_terminal.inverse_video(add_to_bar)

        bar += add_to_bar

    return bar
