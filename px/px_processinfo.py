import sys
import operator

import px_file
import px_process


def find_process_by_pid(pid, processes):
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


def print_process_subtree(process, indentation):
    print("{}{}:{}".format("  " * indentation, process.pid, process.get_command()))
    for child in sorted(process.children, key=operator.attrgetter("pid")):
        print_process_subtree(child, indentation + 1)


def print_process_tree(process):
    # List all parents up to the top
    parents = []
    here = process
    while here.parent is not None:
        parents.append(here.parent)
        here = here.parent

    # Print all parents
    indentation = 0
    for parent in reversed(parents):
        print("{}{}:{}".format("  " * indentation, parent.pid, parent.get_command()))
        indentation += 1

    # Print ourselves
    print("{}{}:{}".format(
        "--" * (indentation - 1) + "> ", process.pid, process.get_command()))
    indentation += 1

    # Print all our child trees
    for child in sorted(process.children, key=operator.attrgetter("pid")):
        print_process_subtree(child, indentation)


def print_fds(process):
    files = px_file.get_all()
    files_for_process = filter(lambda f: f.pid == process.pid, files)

    print("Open files:")
    for file in sorted(files_for_process, key=operator.attrgetter("name")):
        # FIXME: Print which other processes pipes and domain sockets end up in,
        # and if possible who's reading or writing them.

        print("  " + file.name)

    # FIXME: If we were unable to find all information we wanted, hint the user
    # to sudo us next time
    pass


def print_process_info(pid):
    processes = px_process.get_all()
    process = find_process_by_pid(pid, processes)
    if not process:
        sys.stderr.write("No such PID: {}\n".format(pid))
        exit(1)

    print_command_line(process)

    # Print a process tree with all PID's parents and all its children
    print("")
    print_process_tree(process)

    # FIXME: List all files PID has open
    print("")
    print_fds(process)
