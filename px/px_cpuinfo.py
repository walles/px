import os
import errno
import platform
import subprocess

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import Optional  # NOQA
    from typing import Tuple # NOQA
    from typing import List # NOQA
    from six import text_type # NOQA

def get_core_count():
    # type: () -> Tuple[int,int]
    """
    Count the number of cores in the system.

    Returns a tuple (physical, logical) with counts of physical and logical
    cores.
    """
    return_me = get_core_count_from_proc_cpuinfo()
    if return_me is not None:
        return return_me

    return_me = get_core_count_from_sysctl()
    if return_me is not None:
        return return_me

    uname = str(platform.uname())
    platform = uname + " Python " + sys.version

    raise IOError("Unable to get cores info " + platform)


def get_core_count_from_proc_cpuinfo(proc_cpuinfo="/proc/cpuinfo"):
    # type: (str) -> Optional[Tuple[int,int]]
    """
    Count the number of cores in /proc/cpuinfo.

    Returns a tuple (physical, logical) with counts of physical and logical
    cores.
    """
    # Note the ending spaces, they must be there for number extraction to work!
    PROCESSOR_NO_PREFIX = 'processor\t: '
    CORE_ID_PREFIX = 'core id\t\t: '

    core_ids = set()
    max_processor_no = 0
    try:
        with open(proc_cpuinfo) as f:
            for line in f:
                if line.startswith(PROCESSOR_NO_PREFIX):
                    processor_no = int(line[len(PROCESSOR_NO_PREFIX):])
                    max_processor_no = max(processor_no, max_processor_no)
                elif line.startswith(CORE_ID_PREFIX):
                    core_id = int(line[len(CORE_ID_PREFIX)])
                    core_ids.add(core_id)
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # /proc/cpuinfo not found, we're probably not on Linux
            return None

        raise

    physical = len(core_ids)
    logical = max_processor_no + 1
    if physical == 0:
        # I get this on my cell phone
        physical = logical
    return (physical, logical)


def get_core_count_from_sysctl():
    # type: () -> Optional[Tuple[int,int]]
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]

    try:
        sysctl = subprocess.Popen(["sysctl", 'hw'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env=env)
    except (IOError, OSError) as e:
        if e.errno == errno.ENOENT:
            # sysctl not found, we're probably not on OSX
            return None

        raise

    sysctl_stdout = sysctl.communicate()[0].decode('utf-8')
    sysctl_lines = sysctl_stdout.split('\n')

    physical, logical = parse_sysctl_output(sysctl_lines)
    if physical is None or logical is None:
        # On Linux, sysctl exists but it doesn't contain the values we want
        return None

    return (physical, logical)


def parse_sysctl_output(sysctl_lines):
    # type: (List[text_type]) -> Tuple[Optional[int],Optional[int]]

    # Note the ending spaces, they must be there for number extraction to work!
    PHYSICAL_PREFIX = 'hw.physicalcpu: '
    LOGICAL_PREFIX = 'hw.logicalcpu: '

    physical = None
    logical = None
    for line in sysctl_lines:
        if line.startswith(PHYSICAL_PREFIX):
            physical = int(line[len(PHYSICAL_PREFIX):])
        elif line.startswith(LOGICAL_PREFIX):
            logical = int(line[len(LOGICAL_PREFIX):])

    return (physical, logical)
