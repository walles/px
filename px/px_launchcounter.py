import sys
import operator

from . import px_terminal

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from . import px_process   # NOQA
    from six import text_type  # NOQA
    from typing import List    # NOQA
    from typing import Dict    # NOQA
    from typing import Optional  # NOQA


class Launchcounter(object):
    def __init__(self):
        self._binaries = {}  # type: Dict[text_type,int]

        # This is a mapping of binaries into direct and indirect launch counts.
        # The direct one is updated if this process launches a process by
        # itself. The indirect one is updated when a (grand)child of this
        # process launches something.
        self._launchers = {}  # type: Dict[text_type, List[int]]

        # Most recent process snapshot
        self._last_processlist = None  # type: Optional[List[px_process.PxProcess]]

    def _register_launches(self, new_processes):
        # type: (List[px_process.PxProcess]) -> None

        for new_process in new_processes:
            binary = new_process.command
            launch_count = 0
            if binary in self._binaries:
                launch_count = self._binaries[binary]
            launch_count += 1
            self._binaries[binary] = launch_count

            if new_process.parent:
                # Update direct launch count for the parent
                parent_binary = new_process.parent.command
                if parent_binary in self._launchers:
                    counts = self._launchers[parent_binary]
                    counts[0] += 1
                else:
                    self._launchers[parent_binary] = [1, 0]

                # Update indirect launch counts
                indirect_parent = new_process.parent.parent
                while indirect_parent is not None:
                    indirect_binary = indirect_parent.command
                    if indirect_binary in self._launchers:
                        counts = self._launchers[indirect_binary]
                        counts[1] += 1
                    else:
                        self._launchers[indirect_binary] = [0, 1]

                    indirect_parent = indirect_parent.parent

    def _list_new_launches(
        self,
        before,  # type: List[px_process.PxProcess]
        after    # type: List[px_process.PxProcess]
    ):
        # type: (...) -> List[px_process.PxProcess]
        pid2oldProc = {}  # type: Dict[int,px_process.PxProcess]
        for old_proc in before:
            pid2oldProc[old_proc.pid] = old_proc

        new_procs = []  # List[px_process.PxProcess]
        for new_proc in after:
            if new_proc.pid not in pid2oldProc:
                # This is a new process
                new_procs.append(new_proc)
                continue

            old_proc = pid2oldProc[new_proc.pid]
            if old_proc.start_time != new_proc.start_time:
                # This is a new process, PID has been reused
                new_procs.append(new_proc)
                continue

        return new_procs

    def update(self, procs_snapshot):
        # type: (List[px_process.PxProcess]) -> None

        if self._last_processlist is None:
            self._last_processlist = procs_snapshot
            return

        new_processes = self._list_new_launches(self._last_processlist, procs_snapshot)
        self._register_launches(new_processes)

        self._last_processlist = procs_snapshot

    def get_launched_screen_lines(self, rows, columns):
        # type: (int, int) -> List[text_type]

        heading = u'{:>5}  {}'.format('Count', 'Binary')
        heading = px_terminal.get_string_of_length(heading, columns)
        heading = px_terminal.underline_bold(heading)
        lines = [heading]
        for entry in sorted(self._binaries.items(), key=operator.itemgetter(1), reverse=True):
            binary = entry[0]
            count = entry[1]

            # FIXME: Truncate at columns columns
            lines.append('{:>5}  {}'.format(count, binary))
            if len(lines) >= rows:
                break

        if len(lines) < rows:
            lines += [''] * (rows - len(lines))

        return lines

    def get_launchers_screen_lines(self, rows, columns):
        # type: (int, int) -> List[text_type]

        lines = []  # type: List[text_type]
        for entry in sorted(self._launchers.items(), key=operator.itemgetter(1), reverse=True):
            binary = entry[0]
            counts = entry[1]

            # FIXME: Truncate at columns columns
            lines.append('{:>5}  {:>5}  {}'.format(counts[0], counts[1], binary))
            if len(lines) >= rows:
                break

        if len(lines) < rows:
            lines += [''] * (rows - len(lines))

        return lines
