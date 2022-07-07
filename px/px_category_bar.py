import operator

from px import px_terminal

from . import px_process

from typing import Callable, List, Optional
from typing import Dict
from typing import Tuple


def cluster_processes(
    all_processes: List[px_process.PxProcess],
    get_category: Callable[[px_process.PxProcess], str],
    get_value: Callable[[px_process.PxProcess], Optional[float]],
) -> List[Tuple[str, float]]:
    """
    Group processes by category and value, summing up the values in each group.
    """

    names_to_kilobytes: Dict[str, float] = {}
    for process in all_processes:
        category = get_category(process)
        value = get_value(process)
        if value is None:
            continue

        total = names_to_kilobytes.get(category, 0)
        names_to_kilobytes[category] = total + value

    return sorted(names_to_kilobytes.items(), key=operator.itemgetter(1), reverse=True)


def render_bar(bar_length: int, names_and_numbers: List[Tuple[str, float]]) -> str:
    """
    You probably want to use x_by_y() functions at the end of this file instead,
    this is just an internal utility function.
    """

    total = 0.0
    for category in names_and_numbers:
        total += category[1]
    if total == 0:
        return ""

    bar = ""
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

            chars = int(round(bar_length * number * 1.0 / total))
            if chars > 1:
                add_to_bar = px_terminal.get_string_of_length(" " + name, chars)
            else:
                should_alternate = True

        if should_alternate:
            add_to_bar = " "
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


def ram_by_program(length: int, all_processes: List[px_process.PxProcess]) -> str:
    return render_bar(
        length,
        cluster_processes(
            all_processes,
            lambda process: process.command,
            lambda process: process.rss_kb,
        ),
    )


def ram_by_user(length: int, all_processes: List[px_process.PxProcess]) -> str:
    return render_bar(
        length,
        cluster_processes(
            all_processes,
            lambda process: process.username,
            lambda process: process.rss_kb,
        ),
    )


def create_cpu_getter(
    all_processes: List[px_process.PxProcess],
) -> Callable[[px_process.PxProcess], Optional[float]]:
    """
    Getter for cpu_time_seconds if there are any, otherwise for cpu_percent (of
    which we know there are a bunch).
    """
    for process in all_processes:
        if process.cpu_time_seconds is None:
            continue
        if process.cpu_time_seconds > 0:
            return lambda p: p.cpu_time_seconds

    return lambda p: p.cpu_percent


def cpu_by_program(length: int, all_processes: List[px_process.PxProcess]) -> str:
    return render_bar(
        length,
        cluster_processes(
            all_processes,
            lambda process: process.command,
            create_cpu_getter(all_processes),
        ),
    )


def cpu_by_user(length: int, all_processes: List[px_process.PxProcess]) -> str:
    return render_bar(
        length,
        cluster_processes(
            all_processes,
            lambda process: process.username,
            create_cpu_getter(all_processes),
        ),
    )
