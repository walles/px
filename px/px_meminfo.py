import re
import sys
import errno
import platform

from . import px_units
from . import px_terminal
from . import px_exec_util

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type  # NOQA
    from typing import List  # NOQA
    from typing import Tuple  # NOQA
    from typing import Optional  # NOQA


PAGE_SIZE_RE = re.compile(r"page size of ([0-9]+) bytes")

# Example input, from "sysctl vm.swapusage":
# "vm.swapusage: total = 2048.00M  used = 562.75M  free = 1485.25M  (encrypted)"
SWAPUSAGE_RE = re.compile(r".*used = ([0-9.]+)M.*")


def get_meminfo():
    # type: () -> text_type

    total_ram_bytes, wanted_ram_bytes = _get_ram_numbers()
    percentage = (100.0 * wanted_ram_bytes) / total_ram_bytes

    percentage_string = str(int(round(percentage))) + u"%"

    # "80"? I made it up.
    if percentage < 80:
        percentage_string = px_terminal.green(percentage_string)
    elif percentage < 100:
        percentage_string = px_terminal.yellow(percentage_string)
    else:
        percentage_string = px_terminal.red(percentage_string)

    wanted_and_total_string = "".join(
        [
            px_terminal.bold(px_units.bytes_to_string(wanted_ram_bytes)),
            " / ",
            px_terminal.bold(px_units.bytes_to_string(total_ram_bytes)),
        ]
    )

    ram_text = "".join([percentage_string, "  [", wanted_and_total_string, "]"])

    return ram_text


def _get_ram_numbers():
    # type: () -> Tuple[int, int]
    """
    Returns a tuple containing two numbers:
    * Total amount of RAM installed in the machine (in bytes)
    * Wanted amount of RAM by the system (in bytes)

    If wanted > total it generally implies that we're swapping.
    """
    return_me = _get_ram_numbers_from_proc()
    if return_me is not None:
        return return_me

    return_me = _get_ram_numbers_macos()
    if return_me is not None:
        return return_me

    uname = str(platform.uname())
    platform_s = uname + " Python " + sys.version

    raise IOError("Unable to get memory info " + platform_s)


def _update_from_meminfo(base, line, name):
    # type: (Optional[int], text_type, text_type) -> Optional[int]
    if not line.startswith(name + ":"):
        return base

    just_the_number = line[len(name) + 1 : len(line) - 3]

    return int(just_the_number)


def _get_ram_numbers_from_proc(proc_meminfo="/proc/meminfo"):
    # type: (str) -> Optional[Tuple[int, int]]

    total_kb = None  # type: Optional[int]
    available_kb = None  # type: Optional[int]
    free_kb = None  # type: Optional[int]
    buffers_kb = None  # type: Optional[int]
    cached_kb = None  # type: Optional[int]
    swapcached_kb = None  # type: Optional[int]
    swaptotal_kb = None  # type: Optional[int]
    swapfree_kb = None  # type: Optional[int]

    try:
        with open(proc_meminfo) as f:
            for line in f:
                total_kb = _update_from_meminfo(total_kb, line, "MemTotal")
                available_kb = _update_from_meminfo(available_kb, line, "MemAvailable")
                free_kb = _update_from_meminfo(free_kb, line, "MemFree")
                buffers_kb = _update_from_meminfo(buffers_kb, line, "Buffers")
                cached_kb = _update_from_meminfo(cached_kb, line, "Cached")
                swapcached_kb = _update_from_meminfo(swapcached_kb, line, "SwapCached")
                swaptotal_kb = _update_from_meminfo(swaptotal_kb, line, "SwapTotal")
                swapfree_kb = _update_from_meminfo(swapfree_kb, line, "SwapFree")
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # /proc/meminfo not found, we're probably not on Linux
            return None

        raise

    if total_kb is None:
        return None
    if swaptotal_kb is None:
        return None
    if swapfree_kb is None:
        return None
    swapused_kb = swaptotal_kb - swapfree_kb

    if available_kb is not None:
        # Use MemAvailable if we can:
        # https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=34e431b0ae398fc54ea69ff85ec700722c9da773

        ramused_kb = total_kb - available_kb

        return (total_kb * 1024, (swapused_kb + ramused_kb) * 1024)

    if free_kb is None:
        return None
    if buffers_kb is None:
        return None
    if cached_kb is None:
        return None
    if swapcached_kb is None:
        return None

    ramused_kb = total_kb - (free_kb + buffers_kb + cached_kb + swapcached_kb)

    return (total_kb * 1024, (swapused_kb + ramused_kb) * 1024)


def _get_ram_numbers_macos():
    # type: () -> Optional[Tuple[int, int]]
    vm_stat_lines = _get_vmstat_output_lines()
    if vm_stat_lines is None:
        return None

    vmstat_ram = _get_ram_numbers_from_vm_stat_output(vm_stat_lines)
    if vmstat_ram is None:
        return None

    total_ram_bytes, used_ram_bytes = vmstat_ram

    used_swap_bytes = _get_used_swap_bytes_sysctl()

    return (total_ram_bytes, used_ram_bytes + used_swap_bytes)


def _get_vmstat_output_lines():
    # type: () -> Optional[List[text_type]]
    try:
        return px_exec_util.run(["vm_stat"]).splitlines()
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # vm_stat not found, we're probably not on OSX
            return None

        raise


def _get_used_swap_bytes_sysctl():
    # type: () -> int
    stdout = px_exec_util.run(["sysctl", "vm.swapusage"], check_exitcode=True)
    match = SWAPUSAGE_RE.match(stdout.strip())
    if not match:
        raise IOError("No swap usage in 'sysctl vm.swapusage' output: " + stdout)

    return int(float(match.group(1)) * 1024 * 1024)


def _update_if_prefix(base, line, prefix):
    # type: (Optional[int], text_type, text_type) -> Optional[int]
    if not line.startswith(prefix):
        return base

    no_ending_dot = line.rstrip(".")

    return int(no_ending_dot[len(prefix) :])


def _get_ram_numbers_from_vm_stat_output(vm_stat_lines):
    # type: (List[text_type]) -> Optional[Tuple[int, int]]

    # List based on https://apple.stackexchange.com/a/196925/182882
    page_size_bytes = None
    pages_free = None
    pages_active = None
    pages_inactive = None
    pages_speculative = None
    pages_wired = None
    pages_anonymous = None
    pages_purgeable = None
    pages_compressed = None  # "Pages occupied by compressor"
    pages_uncompressed = None  # "Pages stored in compressor"

    for line in vm_stat_lines:
        page_size_match = PAGE_SIZE_RE.search(line)
        if page_size_match:
            page_size_bytes = int(page_size_match.group(1))
            continue

        pages_free = _update_if_prefix(pages_free, line, "Pages free:")
        pages_active = _update_if_prefix(pages_active, line, "Pages active:")
        pages_inactive = _update_if_prefix(pages_inactive, line, "Pages inactive:")
        pages_speculative = _update_if_prefix(
            pages_speculative, line, "Pages speculative:"
        )
        pages_wired = _update_if_prefix(pages_wired, line, "Pages wired down:")
        pages_anonymous = _update_if_prefix(pages_anonymous, line, "Anonymous pages:")
        pages_purgeable = _update_if_prefix(pages_purgeable, line, "Pages purgeable:")
        pages_compressed = _update_if_prefix(
            pages_compressed, line, "Pages occupied by compressor:"
        )
        pages_uncompressed = _update_if_prefix(
            pages_uncompressed, line, "Pages stored in compressor:"
        )

    if page_size_bytes is None:
        return None
    if pages_free is None:
        return None
    if pages_active is None:
        return None
    if pages_inactive is None:
        return None
    if pages_speculative is None:
        return None
    if pages_wired is None:
        return None
    if pages_anonymous is None:
        return None
    if pages_purgeable is None:
        return None
    if pages_compressed is None:
        return None
    if pages_uncompressed is None:
        return None

    # In experiments, this has added up well to the amount of physical RAM in my machine
    total_ram_pages = (
        pages_free
        + pages_active
        + pages_inactive
        + pages_speculative
        + pages_wired
        + pages_compressed
    )

    # This matches what the Activity Monitor shows in macOS 10.15.6
    #
    # For anonymous - purgeable: https://stackoverflow.com/a/36721309/473672
    #
    # FIXME: We want to add swapped out pages to this as well, since those also
    # represent a want for pages.
    wanted_ram_pages = (
        pages_anonymous - pages_purgeable + pages_wired + pages_compressed
    )

    total_ram_bytes = total_ram_pages * page_size_bytes
    wanted_ram_bytes = wanted_ram_pages * page_size_bytes

    return (total_ram_bytes, wanted_ram_bytes)
