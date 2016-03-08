import sys
import errno
import operator

import os
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
    print(array[0])
    for parameter in array[1:]:
        if parameter == "":
            # Print empty parameters as "", otherwise the printout just looks
            # broken.
            parameter = '""'
        print("  " + parameter)


def print_process_subtree(process, indentation):
    print("  " * indentation + str(process))
    for child in sorted(process.children, key=operator.attrgetter("lowercase_command", "pid")):
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
        print("  " * indentation + str(parent))
        indentation += 1

    # Print ourselves
    print("--" * (indentation - 1) + "> " + str(process))
    indentation += 1

    # Print all our child trees
    for child in sorted(process.children, key=operator.attrgetter("lowercase_command", "pid")):
        print_process_subtree(child, indentation)


def get_other_end_pids(file, files):
    """Locate the other end of a pipe / domain socket"""
    name = file.plain_name
    if name.startswith("->"):
        # With lsof 4.87 on OS X 10.11.3, pipe and socket names start with "->",
        # but their endpoint names don't. Strip initial "->" from name before
        # scanning for it.
        name = name[2:]

    pids = set()
    for candidate in files:
        # The other end of the socket / pipe is encoded in the DEVICE field of
        # lsof's output ("view source" in your browser to see the conversation):
        # http://www.justskins.com/forums/lsof-find-both-endpoints-of-a-unix-socket-123037.html
        if candidate.device == name:
            pids.add(candidate.pid)
        if candidate.plain_name.replace("->", "") == file.device:
            pids.add(candidate.pid)

        if candidate.name != file.name:
            continue

        if file.access == 'w' and candidate.access == 'r':
            # On Linux, this is how we identify named FIFOs
            pids.add(candidate.pid)

        if file.access == 'r' and candidate.access == 'w':
            # On Linux, this is how we identify named FIFOs
            pids.add(candidate.pid)

        if file.device_number() is not None:
            if file.device_number() == candidate.device_number():
                pids.add(candidate.pid)

    return pids


def create_fake_process(pid=None, name=None):
    """Fake a process with a useable name"""
    if pid is None and name is None:
        raise ValueError("At least one of pid and name must be set")

    if name is None:
        name = "PID " + str(pid)

    class FakeProcess(object):
        def __repr__(self):
            return self.name

    process = FakeProcess()
    process.name = name
    process.lowercase_command = name.lower()
    process.pid = pid
    return process


def add_ipc_entry(ipc_map, process, file):
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
    unknown = create_fake_process(
        name="UNKNOWN destinations: Running with sudo might help find out where these go.")
    for file in files_for_process:
        if file.type not in ['PIPE', 'FIFO', 'unix']:
            # Only deal with IPC related files
            continue

        if file.plain_name in ['pipe', '(none)']:
            # These are placeholders, not names, can't do anything with these
            continue

        other_end_pids = get_other_end_pids(file, files)
        if other_end_pids == set([]):
            add_ipc_entry(return_me, unknown, file)
            continue

        for other_end_pid in other_end_pids:
            if other_end_pid == process.pid:
                # Talking to ourselves, never mind
                continue

            other_end_process = pid2process.get(other_end_pid)
            if not other_end_process:
                other_end_process = create_fake_process(pid=other_end_pid)
                pid2process[other_end_pid] = other_end_process
            add_ipc_entry(return_me, other_end_process, file)

    return return_me


def to_relative_start_string(base, relative):
    delta_seconds = relative.start_seconds_since_epoch - base.start_seconds_since_epoch
    delta_string = px_process.seconds_to_str(abs(delta_seconds))
    before_or_after = "before"
    if delta_seconds > 0:
        before_or_after = "after"
    elif delta_seconds == 0:
        delta_string = "just"
        if relative.pid > base.pid:
            before_or_after = "after"
    return "{} was started {} {} {}".format(relative, delta_string, before_or_after, base)


def get_closest_starts(process, all_processes):
    """
    Return the processes that were started closest in time to the base process.

    All processes started within 1s of the base process are returned, or the
    five closest if not at least five were that close.
    """
    closest = set()
    by_temporal_vicinity = sorted(
        all_processes,
        key=lambda p: abs(p.start_seconds_since_epoch -
                          process.start_seconds_since_epoch))

    for close in by_temporal_vicinity:
        delta_seconds = abs(close.start_seconds_since_epoch - process.start_seconds_since_epoch)

        if delta_seconds <= 1:
            closest.add(close)
            continue

        # "5" is arbitrarily chosen, look at the printouts to see if it needs tuning
        if len(closest) > 5:
            break

        closest.add(close)

    closest = filter(lambda p: p is not process, closest)
    closest = sorted(closest, key=operator.attrgetter('start_seconds_since_epoch', 'pid'))
    return closest


def print_processes_started_at_the_same_time(process, all_processes):
    print("Other processes started close to " + str(process) + ":")
    for close in get_closest_starts(process, all_processes):
        print("  " + to_relative_start_string(process, close))


def print_fds(process, pid2process):
    files = px_file.get_all()
    files_for_process = filter(lambda f: f.pid == process.pid, files)

    print("Network connections:")
    # FIXME: Print "nothing found" or something if we don't find anything to put
    # here, maybe with a hint to run as root if we think that would help.
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
    for process in sorted(ipc_map.keys(), key=operator.attrgetter("lowercase_command", "pid")):
        print("  " + str(process))
        channels = ipc_map[process]
        channel_names = set()
        channel_names.update(map(lambda c: c.name, channels))
        for channel_name in sorted(channel_names):
            print("    " + channel_name)

    print("")
    print("For a list of all open files, do \"lsof -p {0}\", "
          "or \"watch lsof -p {0}\" for a live view.".format(process.pid))

    if os.getuid() != 0:
        print("")
        print("NOTE: This information might be incomplete, "
              "running as root sometimes produces better results.")


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

    print("")
    print_processes_started_at_the_same_time(process, processes)

    # List all files PID has open
    print("")
    try:
        print_fds(process, pid2process)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        print("Can't list IPC / network sockets, make sure \"lsof\" is installed and in your $PATH")
