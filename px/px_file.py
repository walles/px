import socket
import subprocess

import os


class PxFile(object):
    def __init__(self):
        self._device_number = None

    def __repr__(self):
        # The point of implementing this method is to make the py.test output
        # more readable.
        return str(self.pid) + ":" + str(self)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self.__dict__.items()))

    def __str__(self):
        if self.type == "REG":
            return self.name

        name = self.name
        listen_suffix = ''
        if self.type in ['IPv4', 'IPv6']:
            local, remote_endpoint = self.get_endpoints()
            if not remote_endpoint:
                listen_suffix = ' (LISTEN)'

            name = self._resolve_name()

        # Decorate non-regular files with their type
        return "[" + self.type + "] " + name + listen_suffix

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

        if self.type == 'FIFO' and self.name == 'pipe':
            # This is just a label that can be shared by several pipes on Linux,
            # we can't use it to identify a pipe.
            return None

        if self.type == 'PIPE' and self.name == '(none)':
            # This is just a label that can be shared by several pipes on OS X,
            # we can't use it to identify a pipe.
            return None

        # On OS X, pipes are presented as PIPEs and lack inodes, but they
        # compensate by having unique names.
        return self.name

    def get_endpoints(self):
        """
        Returns a (local,remote) tuple. They represent the local and the remote
        endpoints of a network connection.

        This method will never return None, but both local and remote can be
        None in case this isn't a network connection for example.
        """
        if self.type not in ['IPv4', 'IPv6']:
            return (None, None)

        local = None
        remote = None

        split_name = self.name.split('->')
        local = split_name[0]

        # Turn "localhost:ipp (LISTEN)" into "ipp" and nothing else
        local = local.split(' ')[0]
        if '*' in local:
            # We can't match against this endpoint
            local = None

        if len(split_name) == 2:
            remote = split_name[1]

        return (local, remote)


def resolve_endpoint(endpoint):
    """
    Resolves "127.0.0.1:portnumber" into "localhost:portnumber".
    """
    # Find the rightmost :, necessary for IPv6 addresses
    splitindex = endpoint.rfind(':')
    if splitindex == -1:
        return endpoint

    address = endpoint[0:splitindex]
    if address[0] == '[' and address[-1] == ']':
        # This is how lsof presents IPv6 addresses
        address = address[1:-1]

    port = endpoint[splitindex + 1:]

    try:
        return socket.gethostbyaddr(address)[0] + ":" + port
    except Exception:
        # Lookup failed for whatever reason, give up
        return endpoint


def call_lsof():
    """
    Call lsof and return the result as one big string
    """
    env = os.environ.copy()
    if "LANG" in env:
        del env["LANG"]

    # See OUTPUT FOR OTHER PROGRAMS: http://linux.die.net/man/8/lsof
    # Output lines can be in one of two formats:
    # 1. "pPID@" (with @ meaning NUL)
    # 2. "fFD@aACCESSMODE@tTYPE@nNAME@"
    lsof = subprocess.Popen(["lsof", '-n', '-F', 'fnaptd0i'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    return lsof.communicate()[0].decode('utf-8')


def lsof_to_files(lsof, file_types=None):
    pid = None
    file = None
    files = []
    for shard in lsof.split('\0'):
        if shard[0] == "\n":
            # Some shards start with newlines. Looks pretty when viewing the
            # lsof output in less, but makes the parsing code have to deal with
            # it.
            shard = shard[1:]

        if not shard:
            # The output ends with a single newline, which we just stripped away
            break

        filetype = shard[0]
        value = shard[1:]

        if filetype == 'p':
            pid = int(value)
        elif filetype == 'f':
            file = PxFile()
            file.fd = value
            file.pid = pid
            file.type = "??"
            file.device = None
            file.inode = None

            if not files:
                # No files, just add the new one
                files.append(file)
            elif not file_types:
                # No filter specified
                files.append(file)
            elif files[-1].type in file_types:
                files.append(file)
            else:
                # Overwrite the last file since it's of the wrong type
                files[-1] = file
        elif filetype == 'a':
            file.access = {
                ' ': None,
                'r': "r",
                'w': "w",
                'u': "rw"}[value]
        elif filetype == 't':
            file.type = value
        elif filetype == 'd':
            file.device = value
        elif filetype == 'n':
            file.name = value
        elif filetype == 'i':
            file.inode = value

        else:
            raise Exception("Unhandled type <{}> for shard <{}>".format(filetype, shard))

    return files


def get_all(file_types=None):
    """
    Get all files.

    If a file_types array is specified, only files of the listed types will be
    returned.
    """
    return set(lsof_to_files(call_lsof(), file_types))
