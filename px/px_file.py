import subprocess

import os


class PxFile(object):
    def __init__(self):
        self._device_number = None

    def __repr__(self):
        # I guess this is really what __str__ should be doing, but the point of
        # implementing this method is to make the py.test output more readable,
        # and py.test calls repr() and not str().
        return str(self.pid) + ":" + self.name

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(frozenset(self.__dict__.items()))

    def _set_name(self, name):
        self.name = name
        self.plain_name = name
        if self.type != "REG":
            # Decorate non-regular files with their type
            self.name = "[" + self.type + "] " + self.name

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

        split_name = self.plain_name.split('->')
        local = split_name[0]

        # Turn "localhost:ipp (LISTEN)" into "ipp" and nothing else
        local = local.split(' ')[0]
        if '*' in local:
            # We can't match against this endpoint
            local = None

        if len(split_name) == 2:
            remote = split_name[1]

        return (local, remote)


def device_to_number(device):
    if device is None:
        return None

    number = int(device, 16)
    if number == 0:
        # 0x000lotsofmore000 is what we get on lsof 4.86 and Linux 4.2.0
        # when lsof doesn't have root privileges
        return None

    return number


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
    lsof = subprocess.Popen(["lsof", '-F', 'fnaptd0'],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env)
    return lsof.communicate()[0]


def lsof_to_files(lsof):
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

        type = shard[0]
        value = shard[1:]

        if type == 'p':
            pid = int(value)
        elif type == 'f':
            file = PxFile()
            file.fd = value
            file.pid = pid
            file.type = "??"
            file.device = None
            file.device_number = None
            files.append(file)
        elif type == 'a':
            file.access = {
                ' ': None,
                'r': "r",
                'w': "w",
                'u': "rw"}[value]
        elif type == 't':
            file.type = value
        elif type == 'd':
            file.device = value
            file.device_number = device_to_number(value)
        elif type == 'n':
            file._set_name(value)

        else:
            raise Exception("Unhandled type <{}> for shard <{}>".format(type, shard))

    return files


def get_all():
    return set(lsof_to_files(call_lsof()))
