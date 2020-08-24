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
    total_ram_bytes = _get_total_ram_from_sysctl()
    if total_ram_bytes is None:
        return None

    wanted_ram_bytes = _get_wanted_ram_bytes_from_vm_stat()
    if wanted_ram_bytes is None:
        return None

    return (total_ram_bytes, wanted_ram_bytes)


def _get_total_ram_from_sysctl():
    # type: () -> Optional[int]
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]

    try:
        sysctl = subprocess.Popen(["sysctl", '-n', 'hw.memsize'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env=env)
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # sysctl not found, we're probably not on OSX
            return None

        raise

    sysctl_stdout = sysctl.communicate()[0].decode('utf-8')
    sysctl_lines = sysctl_stdout.split('\n')

    return int(sysctl_lines[0])


def _get_wanted_ram_bytes_from_vm_stat():
    # type: () -> Optional[int]

    # FIXME: Unimplemented
    return 1234567890
