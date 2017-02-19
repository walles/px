import os
import errno
import subprocess


def get_core_count():
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

    return None


def get_core_count_from_proc_cpuinfo(proc_cpuinfo="/proc/cpuinfo"):
    pass


def get_core_count_from_sysctl():
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]

    try:
        sysctl = subprocess.Popen(["sysctl", 'hw'],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  env=env)
    except OSError as e:
        if e.errno == errno.ENOENT:
            # sysctl not found, we're probably not on OSX
            return None

        raise

    sysctl_stdout = sysctl.communicate()[0].decode('utf-8')
    sysctl_lines = sysctl_stdout.split('\n')

    # Note the ending spaces, they must be there for number extraction to work!
    PHYSICAL_PREFIX = 'hw.physicalcpu: '
    LOGICAL_PREFIX = 'hw.logicalcpu: '

    physical = None
    logical = None
    for line in sysctl_lines:
        if line.startswith(PHYSICAL_PREFIX):
            physical = int(line[len(PHYSICAL_PREFIX):])
        elif line.startswith(LOGICAL_PREFIX):
            logical = int(line[len(LOGICAL_PREFIX)])

    return (physical, logical)
