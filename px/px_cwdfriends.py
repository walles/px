from . import px_process
from . import px_file
from typing import List
from typing import Dict
from typing import Optional


def _strip_leading_dash(process: px_process.PxProcess) -> str:
    key = process.command
    if key.startswith("-"):
        key = key[1:]
    return key


class PxCwdFriends:
    def __init__(
        self,
        process: px_process.PxProcess,
        all_processes: List[px_process.PxProcess],
        all_files: List[px_file.PxFile],
    ) -> None:

        pid_to_process: Dict[int, px_process.PxProcess] = {}
        for p in all_processes:
            pid_to_process[p.pid] = p

        # Cwd can be None if lsof and process listing are out of sync
        self.cwd: Optional[str] = None

        cwd_to_processes: Dict[str, List[px_process.PxProcess]] = {}
        for current_file in all_files:
            if not current_file.name:
                continue

            if current_file.fdtype != "cwd":
                continue

            if current_file.pid == process.pid:
                self.cwd = current_file.name

            if current_file.name == "/":
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
            friends: List[px_process.PxProcess] = []
        elif self.cwd in cwd_to_processes:
            friends = cwd_to_processes[self.cwd]
        else:
            friends = []

        if process in friends:
            friends.remove(process)

        # Sort primarily by command and secondarily by PID
        friends = sorted(friends, key=lambda friend: friend.pid)
        friends = sorted(friends, key=_strip_leading_dash)
        self.friends: List[px_process.PxProcess] = friends
