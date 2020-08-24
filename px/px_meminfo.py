import os
import sys
import errno
import platform
import subprocess

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type    # NOQA
    from typing import Tuple     # NOQA
    from typing import Optional  # NOQA


def get_meminfo():
    # type: () -> text_type

    total_ram_bytes, wanted_ram_bytes = _get_ram_numbers()
    percentage = (100 * wanted_ram_bytes) // total_ram_bytes

    return str(percentage) + "%"


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

    return_me = _get_ram_numbers_from_sysctl_and_vm_stat()
    if return_me is not None:
        return return_me

    uname = str(platform.uname())
    platform_s = uname + " Python " + sys.version

    raise IOError("Unable to get memory info " + platform_s)


def _get_ram_numbers_from_proc(proc_meminfo="/proc/meminfo"):
    # type: (str) -> Optional[Tuple[int, int]]
    try:
        with open(proc_meminfo) as f:
            for line in f:
                # FIXME: Write code here
                pass
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # /proc/meminfo not found, we're probably not on Linux
            return None

        raise

    raise Exception("FIXME: Not implemented")


def _get_ram_numbers_from_sysctl_and_vm_stat():
    # type: () -> Optional[Tuple[int, int]]

    # List based on https://apple.stackexchange.com/a/196925/182882
    page_size_bytes = None
    pages_free = None
    pages_active = None
    pages_inactive = None
    pages_speculative = None
    pages_wired = None
    pages_uncompressed = None  # "Pages stored in compressor"

    )))FIXME: Call vm_stat and populate the variables

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
    if pages_uncompressed is None:
        return None

    total_ram_pages = \
        pages_free + pages_active + pages_inactive + pages_speculative + pages_wired
    wanted_ram_pages = \
        pages_active + pages_wired + pages_uncompressed

    total_ram_bytes = total_ram_pages * page_size_bytes
    wanted_ram_bytes = wanted_ram_pages * page_size_bytes

    return (total_ram_bytes, wanted_ram_bytes)
