from . import px_file
from . import px_process
from typing import Set
from typing import List
from typing import Dict
from typing import Text
from typing import MutableMapping
from typing import Iterable
from typing import TypeVar
from typing import Optional

T = TypeVar("T")
S = TypeVar("S")

FILE_TYPES = ["PIPE", "FIFO", "unix", "IPv4", "IPv6"]


class PeerProcess:
    def __init__(self, name: Optional[Text] = None, pid: Optional[int] = None) -> None:
        if not name:
            if pid is None:
                raise ValueError("Either pid, name or both must be set")
            name = "PID " + str(pid)
        else:
            if pid is not None:
                name += "(" + str(pid) + ")"

        self.name: Text = name
        self.pid: Optional[int] = pid

    def __repr__(self):
        return self.name

    def __hash__(self):
        return self.name.__hash__()

    def __str__(self):
        return self.name


class IpcMap:
    # pylint: disable=attribute-defined-outside-init
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

    def __init__(
        self,
        process: px_process.PxProcess,
        files: Iterable[px_file.PxFile],
        processes: Iterable[px_process.PxProcess],
        is_root: bool,
    ) -> None:

        # On Linux, lsof reports the same open file once per thread of a
        # process. Putting the files in a set gives us each file only once.
        files = set(files)

        self._own_files = list(
            filter(lambda f: f.pid == process.pid and f.fd is not None, files)
        )

        # Only deal with IPC related files
        self.files = list(filter(lambda f: f.type in FILE_TYPES, files))

        self.process = process
        self.processes = processes
        self.ipc_files_for_process = list(
            filter(lambda f: f.pid == self.process.pid, self.files)
        )

        self._map: MutableMapping[PeerProcess, Set[px_file.PxFile]] = {}
        self._create_mapping()

        self.fds = self._create_fds(is_root)

    def _create_fds(self, is_root: bool) -> Dict[int, str]:
        """
        Describe standard FDs open by this process; the mapping is from FD number to
        FD description.

        The returned dict will always contain entries for 0, 1 and 2.

        In theory this method could easily be modified to go through all fds, not
        just the standard ones, but that can get us lots more DNS lookups, and
        take a lot of time. If you do want to try it, just drop all the "if fd
        not in [0, 1, 2]: continue"s and benchmark it on not-cached IP addresses.
        """
        fds = {}

        if not self._own_files:
            for fd in [0, 1, 2]:
                fds[fd] = "<unavailable, running px as root might help>"
            return fds

        for fd in [0, 1, 2]:
            fds[fd] = "<closed>"

        for file in self._own_files:
            if file.fd not in [0, 1, 2]:
                continue

            fds[file.fd] = str(file)

            if file.type in FILE_TYPES:
                excuse = "destination not found, try running px as root"
                if is_root:
                    excuse = "not connected"
                name: Optional[str] = file.name
                if not name:
                    name = file.device
                if name and name.startswith("->"):
                    name = name[2:]
                fds[file.fd] = f"[{file.type}] <{excuse}> ({name})"

        # Traverse network connections and update FDs as required
        for network_connection in self.network_connections:
            if network_connection.fd is None:
                continue
            if network_connection.fd not in [0, 1, 2]:
                continue
            fds[network_connection.fd] = str(network_connection)

        # Traverse our IPC structure and update FDs as required
        for target in self.keys():  # pylint: disable=consider-using-dict-items
            for link in self[target]:
                if link.fd is None:
                    # No FD, never mind
                    continue
                if link.fd not in [0, 1, 2]:
                    continue

                # FIXME: If this is a PIPE/FIFO leading to ourselves we should say that
                # FIXME: If this is an unconnected PIPE/FIFO, we should say that

                name = link.name
                if name and name.startswith("->"):
                    name = name[2:]
                fds[link.fd] = f"[{link.type}] -> {target} ({name})"

        return fds

    def _create_mapping(self) -> None:
        self._create_indices()

        unknown = PeerProcess(
            name="UNKNOWN destinations: Running with sudo might help find out where these go"
        )

        network_connections = set()
        for file in self.ipc_files_for_process:
            if file.type in ["FIFO", "PIPE"] and not file.fifo_id():
                # Unidentifiable FIFO, just ignore this
                continue

            other_end_pids = self._get_other_end_pids(file)
            if not other_end_pids:
                if file.type in ["IPv4", "IPv6"]:
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
                    other_end_process = PeerProcess(pid=other_end_pid)
                    self._pid2process[other_end_pid] = other_end_process
                self.add_ipc_entry(other_end_process, file)

        self.network_connections: Set[px_file.PxFile] = network_connections

    def _create_indices(self) -> None:
        """
        Creates indices used by _get_other_end_pids()
        """
        self._pid2process = create_pid2process(self.processes)

        self._device_to_pids: MutableMapping[str, List[int]] = {}
        self._name_to_pids: MutableMapping[str, List[int]] = {}
        self._name_to_files: MutableMapping[str, List[px_file.PxFile]] = {}
        self._device_number_to_files: MutableMapping[int, List[px_file.PxFile]] = {}
        self._fifo_id_and_access_to_pids: MutableMapping[str, List[int]] = {}
        self._local_endpoint_to_pid: MutableMapping[str, int] = {}
        for file in self.files:
            if file.device is not None:
                add_arraymapping(self._device_to_pids, file.device, file.pid)

            if file.name:
                add_arraymapping(self._name_to_pids, file.name, file.pid)
                add_arraymapping(self._name_to_files, file.name, file)

            local_endpoint, _ = file.get_endpoints()
            if local_endpoint:
                self._local_endpoint_to_pid[local_endpoint] = file.pid

            device_number = file.device_number()
            if device_number is not None:
                add_arraymapping(self._device_number_to_files, device_number, file)

            if file.access is not None and file.type == "FIFO":
                fifo_id = file.fifo_id()
                if fifo_id:
                    add_arraymapping(
                        self._fifo_id_and_access_to_pids,
                        fifo_id + file.access,
                        file.pid,
                    )

    def _get_other_end_pids(self, file: px_file.PxFile) -> Iterable[int]:
        """Locate the other end of a pipe / domain socket"""
        if file.type in ["IPv4", "IPv6"]:
            _, remote = file.get_endpoints()
            if remote is None:
                return []

            pid = self._local_endpoint_to_pid.get(remote)
            if pid:
                return [pid]
            return []

        name = file.name
        if name and name.startswith("->"):
            # With lsof 4.87 on OS X 10.11.3, pipe and socket names start with "->",
            # but their endpoint names don't. Strip initial "->" from name before
            # scanning for it.
            name = name[2:]

        file_device_with_arrow = None
        if file.device is not None:
            file_device_with_arrow = "->" + file.device

        pids: Set[int] = set()

        # The other end of the socket / pipe is encoded in the DEVICE field of
        # lsof's output ("view source" in your browser to see the conversation):
        # http://www.justskins.com/forums/lsof-find-both-endpoints-of-a-unix-socket-123037.html
        if name:
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
        if fifo_id and file.access and file.type == "FIFO":
            # On Linux, this is how we trace FIFOs
            opposing_access = {"r": "w", "w": "r"}.get(file.access)
            if opposing_access:
                name_and_opposing_access = fifo_id + opposing_access
                matching_pids = self._fifo_id_and_access_to_pids.get(
                    name_and_opposing_access
                )
                if matching_pids:
                    pids.update(matching_pids)

        return pids

    def add_ipc_entry(self, process: PeerProcess, file: px_file.PxFile) -> None:
        """
        Note that we're connected to process via file
        """
        if process not in self._map:
            self._map[process] = set()

        self._map[process].add(file)

    def keys(self) -> Iterable[PeerProcess]:
        """
        Returns a set of other px_processes this process is connected to
        """
        return self._map.keys()

    def __getitem__(self, process: PeerProcess) -> Set[px_file.PxFile]:
        """
        Returns a set of px_files through which we're connected to the px_process
        """
        return self._map.__getitem__(process)


def create_pid2process(
    processes: Iterable[px_process.PxProcess],
) -> MutableMapping[int, PeerProcess]:
    pid2process: MutableMapping[int, PeerProcess] = {}
    for process in processes:
        # Guard against duplicate PIDs
        assert process.pid not in pid2process

        pid2process[process.pid] = PeerProcess(name=process.command, pid=process.pid)

    return pid2process


def add_arraymapping(mapping: MutableMapping[S, List[T]], key: S, value: T) -> None:
    array = mapping.setdefault(key, [])
    array.append(value)
