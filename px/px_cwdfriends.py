import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process     # NOQA
    from . import px_file        # NOQA
    from typing import List      # NOQA
    from typing import Dict      # NOQA
    from typing import Optional  # NOQA
    from six import text_type    # NOQA


def _strip_leading_dash(process):
    # type: (px_process.PxProcess) -> text_type
    key = process.command
    if key.startswith("-"):
        key = key[1:]
    return key


class PxCwdFriends(object):
    def __init__(self, process, all_processes, all_files):
        # type: (px_process.PxProcess, List[px_process.PxProcess], List[px_file.PxFile]) -> None

        pid_to_process = {}  # type: Dict[int, px_process.PxProcess]
        for p in all_processes:
            pid_to_process[p.pid] = p

        # Cwd can be None if lsof and process listing are out of sync
        self.cwd = None  # type: Optional[text_type]

        cwd_to_processes = {}  # type: Dict[text_type, List[px_process.PxProcess]]
        for current_file in all_files:
            if not current_file.name:
                continue

            if current_file.fdtype != 'cwd':
                continue

            if current_file.pid == process.pid:
                self.cwd = current_file.name

            if current_file.name == '/':
                # This is too common, no point in doing this one
                continue

            file_processes = cwd_to_processes.get(current_file.name)
            if file_processes is None:
                file_processes = []

            file_process = pid_to_process.get(current_file.pid)
            if file_process is not None:
                # Process could be None because there's no way for uss to get a process listing
                # a file listing that can be guaranteed to be in sync
                file_processes.append(file_process)
                cwd_to_processes[current_file.name] = file_processes

        if self.cwd is None:
            friends = []  # type: List[px_process.PxProcess]
        elif self.cwd in cwd_to_processes:
            friends = cwd_to_processes[self.cwd]
        else:
            friends = []

        if process in friends:
            friends.remove(process)

        # Sort primarily by command and secondarily by PID
        friends = sorted(friends, key=lambda friend: friend.pid)
        friends = sorted(friends, key=_strip_leading_dash)
        self.friends = friends  # type: List[px_process.PxProcess]
