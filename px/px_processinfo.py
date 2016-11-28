import sys
import errno
import datetime
import operator

import os
from . import px_file
from . import px_process
from . import px_ipc_map
from . import px_loginhistory


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


def print_process_subtree(process, indentation, lines):
    lines.append(("  " * indentation + str(process), process))
    for child in sorted(process.children, key=operator.attrgetter("lowercase_command", "pid")):
        print_process_subtree(child, indentation + 1, lines)


def print_process_tree(process):
    # Contains tuples; the line to print and the process that line is for
    lines_and_processes = []

    # List all parents up to the top
    parents = []
    here = process
    while here.parent is not None:
        parents.append(here.parent)
        here = here.parent

    # Print all parents
    indentation = 0
    for parent in reversed(parents):
        lines_and_processes.append(("  " * indentation + str(parent), parent))
        indentation += 1

    # Print ourselves
    lines_and_processes.append(("--" * (indentation - 1) + "> " + str(process), process))
    indentation += 1

    # Print all our child trees
    for child in sorted(process.children, key=operator.attrgetter("lowercase_command", "pid")):
        print_process_subtree(child, indentation, lines_and_processes)

    # Add an owners column to the right of the tree
    tree_width = max(map(lambda lp: len(lp[0]), lines_and_processes))
    lineformat = "{:" + str(tree_width) + "s}  {}"
    lines = []
    for line_and_process in lines_and_processes:
        line = line_and_process[0]
        owner = line_and_process[1].username
        if line_and_process[1].pid == process.pid:
            sudo_user = process.get_sudo_user()
            if sudo_user:
                owner += ', $SUDO_USER=' + sudo_user

        lines.append(lineformat.format(line, owner))

    print('\n'.join(lines))


def to_relative_start_string(base, relative):
    delta_seconds = base.age_seconds - relative.age_seconds
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
        key=lambda p: abs(p.age_seconds - process.age_seconds))

    for close in by_temporal_vicinity:
        delta_seconds = abs(close.age_seconds - process.age_seconds)

        if delta_seconds <= 1:
            closest.add(close)
            continue

        # "5" is arbitrarily chosen, look at the printouts to see if it needs tuning
        if len(closest) > 5:
            break

        closest.add(close)

    # Remove ourselves from the closest processes list
    closest = filter(lambda p: p is not process, closest)

    # Sort closest processes by age, command and PID in that order
    closest = sorted(closest, key=operator.attrgetter('command', 'pid'))
    closest = sorted(closest, key=operator.attrgetter('age_seconds'), reverse=True)
    return closest


def print_processes_started_at_the_same_time(process, all_processes):
    print("Other processes started close to " + str(process) + ":")
    for close in get_closest_starts(process, all_processes):
        print("  " + to_relative_start_string(process, close))


def print_users_when_process_started(process):
    print("Users logged in when " + str(process) + " started:")
    users = px_loginhistory.get_users_at(process.start_time)
    if not users:
        print('  <Nobody found, either nobody was logged in or the wtmp logs have been rotated>')
        return

    for user in sorted(users):
        print("  " + user)


def print_fds(process, processes):
    # It's true, I measured it myself /johan.walles@gmail.com
    print(datetime.datetime.now().isoformat() +
          ": Now invoking lsof, this can take over a minute on a big system...")

    files = px_file.get_all(px_ipc_map.FILE_TYPES)
    print(datetime.datetime.now().isoformat() +
          ": lsof done, proceeding.")

    ipc_map = px_ipc_map.IpcMap(process, files, processes)

    print("")
    print("Network connections:")
    # FIXME: Print "nothing found" or something if we don't find anything to put
    # here, maybe with a hint to run as root if we think that would help.
    for connection in sorted(ipc_map.network_connections, key=operator.attrgetter("name")):
        print("  " + str(connection))

    print("")
    print("Inter Process Communication:")
    for target in sorted(ipc_map.keys(), key=operator.attrgetter("lowercase_command", "pid")):
        print("  " + str(target))
        channels = ipc_map[target]
        channel_names = set()
        channel_names.update(map(lambda c: str(c), channels))
        for channel_name in sorted(channel_names):
            print("    " + channel_name)

    print("")
    print("For a list of all open files, do \"lsof -p {0}\", "
          "or \"watch lsof -p {0}\" for a live view.".format(process.pid))

    if os.getuid() != 0:
        print("")
        print("NOTE: This information might be incomplete, "
              "running as root sometimes produces better results.")


def print_start_time(process):
    print("{} ago {} was started, at {}.".format(
        process.age_s,
        process.command,
        process.start_time.isoformat(),
    ))

    if process.cpu_time_seconds and process.age_seconds:
        cpu_percent = (100.0 * process.cpu_time_seconds / process.age_seconds)
        print("{:.1f}% has been its average CPU usage since then, or {}/{}".format(
            cpu_percent,
            process.cpu_time_s,
            process.age_s,
        ))


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

    print("")
    print_start_time(process)

    print("")
    print_processes_started_at_the_same_time(process, processes)

    print("")
    print_users_when_process_started(process)

    # List all files PID has open
    print("")
    try:
        print_fds(process, processes)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise
        print("Can't list IPC / network sockets, make sure \"lsof\" is installed and in your $PATH")
