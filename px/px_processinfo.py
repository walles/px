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


def add_ipc_entry(ipc_map, pid, file, pid2process):
    process = pid2process.get(pid)
    if not process:
        # Fake a process with a useable name
        class NamedProcess(object):
            pass

        process = NamedProcess()
        process.name = "PID " + str(pid)
        process.pid = pid
        pid2process[pid] = process

    if process not in ipc_map:
        ipc_map[process] = set()

    ipc_map[process].add(file)


def get_ipc_map(process, files, pid2process):
    """
    Construct a map of process->[channels], where "process" is a process we have
    IPC communication open with, and a channel is a socket or a pipe that we
    have open to that process.
    """

    files_for_process = filter(lambda f: f.pid == process.pid, files)

    return_me = {}
    for file in files_for_process:
        if file.type not in ['PIPE', 'unix']:
            # Only deal with IPC related files
            continue

        other_end = get_other_end(file.plain_name, files)
        if other_end is None:
            # Other end not found, never mind
            # FIXME: Maybe tell the user to sudo us in this case? Or add an
            # "unknown" destination process mentioning sudo?
            continue

        if other_end.pid == process.pid:
            # Talking to ourselves, never mind
            continue

        add_ipc_entry(return_me, other_end.pid, file, pid2process)

    return return_me


def print_fds(process, pid2process):
    # FIXME: Handle lsof not being available on the system
    files = px_file.get_all()
    files_for_process = filter(lambda f: f.pid == process.pid, files)

    print("Network connections:")
    # FIXME: Print "nothing found" or something if we don't find anything to put
    # here, maybe with a hint to install lsof and run as root.
    for file in sorted(files_for_process, key=operator.attrgetter("name")):
        if file.type in ['IPv4', 'IPv6']:
            # Print remote communication
            # FIXME: If this socket is open towards a port on the local machine,
            # can we trace its destination and print that process here?
            print("  " + file.name)
            continue

    print("")
    print("Inter Process Communication:")
    ipc_map = get_ipc_map(process, files, pid2process)
    for process in sorted(ipc_map.keys(), key=operator.attrgetter('pid')):
        print("  " + str(process))
        channels = ipc_map[process]
        for channel in sorted(channels, key=operator.attrgetter("name")):
            print("    " + channel.name)

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
