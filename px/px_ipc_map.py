class IpcMap(object):
    """
    This is a map of process->[channels], where "process" is a process we have
    IPC communication open with, and a channel is a socket or a pipe that we
    have open to that process.
    """

    def __init__(self, process, files, processes):
        self._pid2process = create_pid2process(processes)

        # Only deal with IPC related files
        self.files = filter(
            lambda f: f.type in ['PIPE', 'FIFO', 'unix', 'IPv4', 'IPv6'],
            files)

        self.process = process
        self.files_for_process = filter(lambda f: f.pid == self.process.pid, self.files)

        self._map = {}
        self._create_mapping()

    def _create_mapping(self):
        unknown = create_fake_process(
            name="UNKNOWN destinations: Running with sudo might help find out where these go.")

        for file in self.files_for_process:
            if file.plain_name in ['pipe', '(none)']:
                # These are placeholders, not names, can't do anything with these
                continue

            other_end_pids = self._get_other_end_pids(file)
            if other_end_pids == set([]):
                if file.type in ['IPv4', 'IPv6']:
                    # These are sometimes used for IPC, sometimes not, only report
                    # them if they are.
                    continue

                self.add_ipc_entry(unknown, file)
                continue

            for other_end_pid in other_end_pids:
                if other_end_pid == self.process.pid:
                    # Talking to ourselves, never mind
                    continue

                other_end_process = self._pid2process.get(other_end_pid)
                if not other_end_process:
                    other_end_process = create_fake_process(pid=other_end_pid)
                    self._pid2process[other_end_pid] = other_end_process
                self.add_ipc_entry(other_end_process, file)

    def _get_other_end_pids(self, file):
        """Locate the other end of a pipe / domain socket"""
        name = file.plain_name
        if name.startswith("->"):
            # With lsof 4.87 on OS X 10.11.3, pipe and socket names start with "->",
            # but their endpoint names don't. Strip initial "->" from name before
            # scanning for it.
            name = name[2:]

        file_device_with_arrow = None
        if file.device is not None:
            file_device_with_arrow = "->" + file.device

        pids = set()
        for candidate in self.files:
            # The other end of the socket / pipe is encoded in the DEVICE field of
            # lsof's output ("view source" in your browser to see the conversation):
            # http://www.justskins.com/forums/lsof-find-both-endpoints-of-a-unix-socket-123037.html
            if candidate.device == name:
                pids.add(candidate.pid)
            if candidate.plain_name == file_device_with_arrow:
                pids.add(candidate.pid)

            if candidate.name != file.name:
                continue

            if file.access == 'w' and candidate.access == 'r':
                # On Linux, this is how we identify named FIFOs
                pids.add(candidate.pid)

            if file.access == 'r' and candidate.access == 'w':
                # On Linux, this is how we identify named FIFOs
                pids.add(candidate.pid)

            if file.device_number is not None:
                if file.device_number == candidate.device_number:
                    pids.add(candidate.pid)

        return pids

    def add_ipc_entry(self, process, file):
        if process not in self._map:
            self._map[process] = set()

        self._map[process].add(file)

    def keys(self):
        return self._map.keys()

    def __getitem__(self, index):
        return self._map.__getitem__(index)


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


def create_pid2process(processes):
    pid2process = {}
    for process in processes:
        # Guard against duplicate PIDs
        assert process.pid not in pid2process

        pid2process[process.pid] = process

    return pid2process
