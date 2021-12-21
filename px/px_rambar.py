import sys

from px import px_terminal

from . import px_process

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List  # NOQA
    from typing import Dict  # NOQA
    from typing import Tuple  # NOQA
    from six import text_type  # NOQA


def get_categories(processes):
    # type: (List[px_process.PxProcess]) -> List[Tuple[text_type, int]]
    """
    Group processes by pretty names, keeping track of the total rss_kb in each
    group.

    Return the top three groups in order plus one "other" which is the sum of
    the rest.
    """

    return [("apa", 1000), ("bepa", 300), ("cepa", 200), ("others", 666)]


def rambar(ram_bar_length, processes):
    # type: (int, List[px_process.PxProcess]) -> text_type

    categories = get_categories(processes)

    return px_terminal.get_string_of_length(
        " | ".join(map(lambda t: t[0], categories)), ram_bar_length
    )
