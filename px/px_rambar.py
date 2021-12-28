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


def get_process_categories(all_processes):
    # type: (List[px_process.PxProcess]) -> List[Tuple[text_type, int]]
    """
    Group processes by pretty names, keeping track of the total rss_kb in each
    group.
    """

    names_to_kilobytes = {}  # type: Dict[text_type, int]
    for process in all_processes:
        base_kb = 0
        if process.command in names_to_kilobytes:
            base_kb = names_to_kilobytes[process.command]
        else:
            base_kb = 0

        names_to_kilobytes[process.command] = base_kb + process.rss_kb

    return sorted(names_to_kilobytes.items(), key=operator.itemgetter(1), reverse=True)


def get_user_categories(all_processes):
    # type: (List[px_process.PxProcess]) -> List[Tuple[text_type, int]]
    """
    Group processes by user names, keeping track of the total rss_kb in each
    group.
    """

    names_to_kilobytes = {}  # type: Dict[text_type, int]
    for process in all_processes:
        base_kb = 0
        if process.username in names_to_kilobytes:
            base_kb = names_to_kilobytes[process.username]
        else:
            base_kb = 0

        names_to_kilobytes[process.username] = base_kb + process.rss_kb

    return sorted(names_to_kilobytes.items(), key=operator.itemgetter(1), reverse=True)


def render_bar(bar_length, names_and_numbers):
    # type: (int, List[Tuple[text_type, int]]) -> text_type
    """
    You probably want to use rambar() instead, this is just utility function.
    """

    sum = 0
    for category in names_and_numbers:
        sum += category[1]
    assert sum > 0

    bar = u""
    bar_chars = 0
    chunk_number = -1
    should_alternate = False
    while bar_chars < bar_length:
        chunk_number += 1

        if chunk_number >= len(names_and_numbers):
            # Ran out of names_and_numbers, just start alternating
            should_alternate = True

        if not should_alternate:
            # Show some real data
            name_and_number = names_and_numbers[chunk_number]
            name = name_and_number[0]
            number = name_and_number[1]

            chars = int(round(bar_length * number * 1.0 / sum))
            if chars > 1:
                add_to_bar = px_terminal.get_string_of_length(u" " + name, chars)
            else:
                should_alternate = True

        if should_alternate:
            add_to_bar = u" "
        add_to_bar_chars = len(add_to_bar)

        if chunk_number == 0:
            # First red
            add_to_bar = px_terminal.red(add_to_bar)
        elif chunk_number == 1:
            # Second yellow
            add_to_bar = px_terminal.yellow(add_to_bar)
        elif chunk_number % 2 == 1:
            # Then alternating between inverse video and blue
            add_to_bar = px_terminal.inverse_video(add_to_bar)
        else:
            # chunk_number % 2 == 0
            add_to_bar = px_terminal.blue(add_to_bar)

        assert len(add_to_bar) > 0
        bar += add_to_bar
        bar_chars += add_to_bar_chars

    return bar


def rambar_by_process(ram_bar_length, all_processes):
    # type: (int, List[px_process.PxProcess]) -> text_type
    return render_bar(ram_bar_length, get_process_categories(all_processes))


def rambar_by_user(ram_bar_length, all_processes):
    # type: (int, List[px_process.PxProcess]) -> text_type
    return render_bar(ram_bar_length, get_user_categories(all_processes))
