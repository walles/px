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


def get_other_end(name, files):
    """Locate the other end of a pipe / domain socket"""
    if name.startswith("->"):
        # With lsof 4.87 on OS X 10.11.3, pipe and socket names start with "->",
        # but their endpoint names don't. Strip initial "->" from name before
        # scanning for it.
        name = name[2:]

    for file in files:
        # The other end of the socket / pipe is encoded in the DEVICE field of
        # lsof's output ("view source" in your browser to see the conversation):
        # http://www.justskins.com/forums/lsof-find-both-endpoints-of-a-unix-socket-123037.html
        if file.device == name:
            return file

    return None


def print_fds(process, pid2process):
    # FIXME: Handle lsof not being available on the system
    files = px_file.get_all()
    files_for_process = filter(lambda f: f.pid == process.pid, files)

    print("Communication with other processes:")
    for file in sorted(files_for_process, key=operator.attrgetter("name")):
        if file.type in ['IPv4', 'IPv6']:
            # Print remote communication
            # FIXME: If this socket is open towards a port on the local machine,
            # can we trace its destination and print that process here?
            print("  " + file.name)
            continue

        if file.type not in ['PIPE', 'unix']:
            # Only print files relating us to other local or remote processes
            continue

        other_end = get_other_end(file.plain_name, files)
        if other_end is None:
            # Other end not found, never mind
            # FIXME: Maybe tell the user to sudo us in this case?
            continue

        if other_end.pid == process.pid:
            # Talking to ourselves, never mind
            continue

        other_process = pid2process.get(other_end.pid)
        other_process_description = None
        if other_process is not None:
            other_process_description = str(other_process)
        else:
            other_process_description = "PID " + str(other_process.pid)
        print("  " + file.name)
        print("    " + other_process_description)

    # FIXME: If we were unable to find all information we wanted, hint the user
    # to sudo us next time
    pass


def print_process_info(pid):
    processes = px_process.get_all()

    pid2process = {}
    for process in processes:
        # Guard against duplicate PIDs
        assert process.pid not in pid2process

        pid2process[process.pid] = process

    process = find_process_by_pid(pid, processes)
    if not process:
        sys.stderr.write("No such PID: {}\n".format(pid))
        exit(1)

    print_command_line(process)

    # Print a process tree with all PID's parents and all its children
    print("")
    print_process_tree(process)

    # List all files PID has open
    print("")
    print_fds(process, pid2process)
