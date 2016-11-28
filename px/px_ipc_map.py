FILE_TYPES = ['PIPE', 'FIFO', 'unix', 'IPv4', 'IPv6']


class IpcMap(object):
    """
    This is a map of process->[channels], where "process" is a process we have
    IPC communication open with, and a channel is a socket or a pipe that we
    have open to that process.

    After creating an IpcMap, you can access:
    * ipc_map.network_connections: This is a list of non-IPC network connections
    * ipc_map.keys(): A set of other px_processes this process is connected to
    * ipc_map[px_process]: A set of px_files through which we're connected to the
      px_process
    """

    def __init__(self, process, files, processes):
        # On Linux, lsof reports the same open file once per thread of a
        # process. Putting the files in a set gives us each file only once.
        files = set(files)

        # Only deal with IPC related files
        self.files = list(filter(lambda f: f.type in FILE_TYPES, files))

        self.process = process
        self.processes = processes
        self.files_for_process = list(filter(lambda f: f.pid == self.process.pid, self.files))

        self._map = {}
        self._create_mapping()

    def _create_mapping(self):
        self._create_indices()

        unknown = create_fake_process(
            name="UNKNOWN destinations: Running with sudo might help find out where these go.")

        network_connections = set()
        for file in self.files_for_process:
            if file.type in ['FIFO', 'PIPE'] and not file.fifo_id():
                # Unidentifiable FIFO, just ignore this
                continue

            other_end_pids = self._get_other_end_pids(file)
            if not other_end_pids:
                if file.type in ['IPv4', 'IPv6']:
                    # This is a remote connection
                    network_connections.add(file)
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

        self.network_connections = network_connections

    def _create_indices(self):
        """
        Creates indices used by _get_other_end_pids()
        """
        self._pid2process = create_pid2process(self.processes)

        self._device_to_pids = {}
        self._name_to_pids = {}
        self._name_to_files = {}
        self._device_number_to_files = {}
        self._fifo_id_and_access_to_pids = {}
        self._local_endpoint_to_pid = {}
        for file in self.files:
            if file.device is not None:
                add_arraymapping(self._device_to_pids, file.device, file.pid)

            add_arraymapping(self._name_to_pids, file.name, file.pid)

            add_arraymapping(self._name_to_files, file.name, file)

            local_endpoint, remote = file.get_endpoints()
            if local_endpoint:
                self._local_endpoint_to_pid[local_endpoint] = file.pid

            device_number = file.device_number()
            if device_number is not None:
                add_arraymapping(self._device_number_to_files, device_number, file)

            if file.access is not None and file.type == 'FIFO':
                fifo_id = file.fifo_id()
                if fifo_id:
                    add_arraymapping(self._fifo_id_and_access_to_pids,
                                     fifo_id + file.access, file.pid)

    def _get_other_end_pids(self, file):
        """Locate the other end of a pipe / domain socket"""
        if file.type in ['IPv4', 'IPv6']:
            local, remote = file.get_endpoints()
            if remote is None:
                return []

            pid = self._local_endpoint_to_pid.get(remote)
            if pid:
                return [pid]
            else:
                return []

        name = file.name
        if name.startswith("->"):
            # With lsof 4.87 on OS X 10.11.3, pipe and socket names start with "->",
            # but their endpoint names don't. Strip initial "->" from name before
            # scanning for it.
            name = name[2:]

        file_device_with_arrow = None
        if file.device is not None:
            file_device_with_arrow = "->" + file.device

        pids = set()

        # The other end of the socket / pipe is encoded in the DEVICE field of
        # lsof's output ("view source" in your browser to see the conversation):
        # http://www.justskins.com/forums/lsof-find-both-endpoints-of-a-unix-socket-123037.html
        matching_pids = self._device_to_pids.get(name)
        if matching_pids:
            pids.update(matching_pids)
        if file_device_with_arrow:
            matching_pids = self._name_to_pids.get(file_device_with_arrow)
            if matching_pids:
                pids.update(matching_pids)

        device_number = file.device_number()
        if device_number:
            matching_files = self._device_number_to_files.get(device_number)
            if not matching_files:
                matching_files = []
            for candidate in matching_files:
                if candidate.name == file.name:
                    pids.add(candidate.pid)

        fifo_id = file.fifo_id()
        if fifo_id and file.access and file.type == 'FIFO':
            # On Linux, this is how we trace FIFOs
            opposing_access = {'r': 'w', 'w': 'r'}.get(file.access)
            if opposing_access:
                name_and_opposing_access = fifo_id + opposing_access
                matching_pids = self._fifo_id_and_access_to_pids.get(name_and_opposing_access)
                if matching_pids:
                    pids.update(matching_pids)

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


def add_arraymapping(mapping, key, value):
    array = mapping.setdefault(key, [])
    array.append(value)
