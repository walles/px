import sys

import px_process


def find_pid(pid, processes):
    for process in processes:
        if process.pid == pid:
            return process

    return None


def print_command_line(process):
    """
    Print command line separated by linefeeds rather than space, this adds
    readability to long command lines
    """
    array = process.get_command_line_array()
    print("\n  ".join(array))


def print_process_info(pid):
    processes = px_process.get_all()
    process = find_pid(pid, processes)
    if not process:
        sys.stderr.write("No such PID: {}\n".format(pid))
        exit(1)

    print_command_line(process)

    # FIXME: Print a process tree with all PID's parents and all its children

    # FIXME: List all files PID has open

    # FIXME: List all sockets PID has open, and where they lead

    # FIXME: List all pipes PID has open, and where they lead
