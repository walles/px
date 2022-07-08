import socket

from . import px_exec_util

from typing import Set
from typing import List
from typing import Tuple
from typing import Optional


class PxFile:
    def __init__(self, pid: int, filetype: str) -> None:
        self.fd: Optional[int] = None
        self.pid = pid
        self.type = filetype
        self.name: Optional[str] = None
        self.inode: Optional[str] = None
        self.device: Optional[str] = None
        self.access: Optional[str] = None

        # Example values: "cwd", "txt" and probably others as well
        self.fdtype: Optional[str] = None

    def __repr__(self):
        # The point of implementing this method is to make the py.test output
        # more readable.
        return str(self.pid) + ":" + str(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.name, self.fd, self.fdtype, self.pid))

    def __str__(self):
        if self.type == "REG":
            return self.name

        name = self.name
        listen_suffix = ""
        if self.type in ["IPv4", "IPv6"]:
            _, remote_endpoint = self.get_endpoints()
            if not remote_endpoint:
                listen_suffix = " (LISTEN)"

            name = self._resolve_name()

        # Decorate non-regular files with their type
        if name:
            return "[" + self.type + "] " + name + listen_suffix
        return "[" + self.type + "] " + listen_suffix

    def _resolve_name(self):
        local, remote = self.get_endpoints()
        if not local:
            return self.name

        local = resolve_endpoint(local)
        if not remote:
            return local

        return local + "->" + resolve_endpoint(remote)

    def device_number(self):
        if self.device is None:
            return None

        number = int(self.device, 16)
        if number == 0:
            # 0x000lotsofmore000 is what we get on lsof 4.86 and Linux 4.2.0
            # when lsof doesn't have root privileges
            return None

        return number

    def fifo_id(self):
        if self.inode is not None:
            # On Linux, pipes are presented by lsof as FIFOs. They have unique-
            # per-pipe inodes, so we use them as IDs.
            return self.inode

        if self.type == "FIFO" and self.name == "pipe":
            # This is just a label that can be shared by several pipes on Linux,
            # we can't use it to identify a pipe.
            return None

        if self.type == "PIPE" and self.name == "(none)":
            # This is just a label that can be shared by several pipes on OS X,
            # we can't use it to identify a pipe.
            return None

        # On OS X, pipes are presented as PIPEs and lack inodes, but they
        # compensate by having unique names.
        return self.name

    def get_endpoints(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Returns a (local,remote) tuple. They represent the local and the remote
        endpoints of a network connection.

        This method will never return None, but both local and remote can be
        None in case this isn't a network connection for example.
        """
        if not self.name:
            return (None, None)

        if self.type not in ["IPv4", "IPv6"]:
            return (None, None)

        local = None
        remote = None

        split_name = self.name.split("->")
        local = split_name[0]

        # Turn "localhost:ipp (LISTEN)" into "ipp" and nothing else
        local = local.split(" ")[0]
        if "*" in local:
            # We can't match against this endpoint
            local = None

        if len(split_name) == 2:
            remote = split_name[1]

        return (local, remote)


class PxFileBuilder:
    def __init__(self):
        self.fd: Optional[int] = None
        self.pid: Optional[int] = None
        self.name: Optional[str] = None
        self.type: Optional[str] = None
        self.inode: Optional[str] = None
        self.device: Optional[str] = None
        self.access: Optional[str] = None

        # Example values: "cwd", "txt" and probably others as well
        self.fdtype: Optional[str] = None

    def build(self) -> PxFile:
        assert self.pid is not None
        assert self.type
        pxFile = PxFile(self.pid, self.type)
        pxFile.name = self.name
        pxFile.fd = self.fd
        pxFile.inode = self.inode
        pxFile.device = self.device
        pxFile.access = self.access
        pxFile.fdtype = self.fdtype

        return pxFile

    def __repr__(self):
        return f"PxFileBuilder(pid={self.pid}, name={self.name}, type={self.type})"


def resolve_endpoint(endpoint: str) -> str:
    """
    Resolves "127.0.0.1:portnumber" into "localhost:portnumber".
    """
    # Find the rightmost :, necessary for IPv6 addresses
    splitindex = endpoint.rfind(":")
    if splitindex == -1:
        return endpoint

    address = endpoint[0:splitindex]
    if address[0] == "[" and address[-1] == "]":
        # This is how lsof presents IPv6 addresses
        address = address[1:-1]

    port = endpoint[splitindex + 1 :]
    host = None

    try:
        host = socket.gethostbyaddr(address)[0]
    except Exception:  # pylint: disable=broad-except
        # Lookup failed for whatever reason, give up
        #
        # Catching "Exception" because I am (on 2022may27) unable to figure out
        # from these docs what exceptions can be thrown by that method, if any:
        # https://docs.python.org/3.10/library/socket.html#socket.gethostbyaddr
        return endpoint

    if host == "localhost.localdomain":
        # "localdomain" is just a long word that doesn't add any information
        host = "localhost"

    return host + ":" + port


def call_lsof():
    """
    Call lsof and return the result as one big string
    """
    # See OUTPUT FOR OTHER PROGRAMS: http://linux.die.net/man/8/lsof
    # Output lines can be in one of two formats:
    # 1. "pPID@" (with @ meaning NUL)
    # 2. "fFD@aACCESSMODE@tTYPE@nNAME@"
    return px_exec_util.run(["lsof", "-n", "-F", "fnaptd0i"])


def lsof_to_files(lsof: str) -> List[PxFile]:
    """
    Convert lsof output into a files array.
    """

    pid = None
    file_builder: Optional[PxFileBuilder] = None
    files: List[PxFile] = []
    for shard in lsof.split("\0"):
        if shard[0] == "\n":
            # Some shards start with newlines. Looks pretty when viewing the
            # lsof output in moar, but makes the parsing code have to deal with
            # it.
            shard = shard[1:]

        if not shard:
            # The output ends with a single newline, which we just stripped away
            break

        infotype = shard[0]
        value = shard[1:]

        if infotype == "p":
            pid = int(value)
        elif infotype == "f":
            if file_builder:
                files.append(file_builder.build())
            else:
                file_builder = PxFileBuilder()

            # Reset the file builder object. This operation is on a hot path
            # and doing without an extra object allocation here actually helps.
            file_builder.__init__()  # type: ignore

            if value.isdigit():
                file_builder.fd = int(value)
            else:
                # Words like "cwd", "txt" and probably others as well
                file_builder.fdtype = value
            assert pid is not None
            file_builder.pid = pid
            file_builder.type = "??"
        elif infotype == "a":
            assert file_builder is not None
            access = {" ": None, "r": "r", "w": "w", "u": "rw"}[value]
            file_builder.access = access
        elif infotype == "t":
            assert file_builder is not None
            file_builder.type = value
        elif infotype == "d":
            assert file_builder is not None
            file_builder.device = value
        elif infotype == "n":
            assert file_builder is not None
            file_builder.name = value
        elif infotype == "i":
            assert file_builder is not None
            file_builder.inode = value

        else:
            raise Exception(f"Unhandled type <{infotype}> for shard <{shard}>")

    if file_builder:
        # Don't forget the last file
        files.append(file_builder.build())

    return files


def get_all() -> Set[PxFile]:
    """
    Get all files.

    If a file_types array is specified, only files of the listed types will be
    returned.
    """
    return set(lsof_to_files(call_lsof()))
