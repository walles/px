import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process     # NOQA
    from . import px_file        # NOQA
    from typing import List      # NOQA
    from typing import Dict      # NOQA
    from typing import Optional  # NOQA
    from six import text_type    # NOQA


class PxCwdFriends(object):
    def __init__(self, pid, all_processes, all_files):
        # type: (int, List[px_process.PxProcess], List[px_file.PxFile]) -> None

        pid_to_process = {}  # type: Dict[int, px_process.PxProcess]
        for p in all_processes:
            pid_to_process[p.pid] = p

        # Cwd can be None if lsof and process listing are out of sync
        self.cwd = None  # type: Optional[text_type]

        cwd_to_processes = {}  # type: Dict[text_type, List[px_process.PxProcess]]
        for current_file in all_files:
            if current_file.type != 'cwd':
                continue

            if current_file.name == '/':
                # This is too common, no point in doing this one
                continue

            if current_file.pid == pid:
                self.cwd = current_file.name

            processes = cwd_to_processes.get(current_file.name)
            if processes is None:
                processes = []

            process = pid_to_process.get(current_file.pid)
            if process is not None:
                # Process could be None because there's no way for uss to get a process listing
                # a file listing that can be guaranteed to be in sync
                processes.append(process)
                cwd_to_processes[current_file.name] = processes

        if self.cwd is None:
            friends = []  # type: List[px_process.PxProcess]
        elif self.cwd in cwd_to_processes:
            friends = cwd_to_processes[self.cwd]
        else:
            friends = []

        self.friends = friends  # type: List[px_process.PxProcess]
