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
        return str(self.__dict__).__hash__()

    def _set_name(self, name):
        self.name = name
        self.plain_name = name
        if self.type != "REG":
            # Decorate non-regular files with their type
            self.name = "[" + self.type + "] " + self.name

        localhost_port = None
        target_localhost_port = None
        if self.type in ['IPv4', 'IPv6']:
            split_name = name.split('->')
            localhost_port = split_name[0].split(':')[1]

            # Turn "localhost:ipp (LISTEN)" into "ipp" and nothing else
            localhost_port = localhost_port.split(' ')[0]

            if len(split_name) == 2:
                split_remote = split_name[1].split(':')
                if split_remote[0] == 'localhost':
                    target_localhost_port = split_remote[1]
        if localhost_port == '*':
            # This is sometimes reported for UDP
            localhost_port = None

        # For network connections, this is the local port of the connection
        self.localhost_port = localhost_port

        # For network connections to localhost, this is the target port
        self.target_localhost_port = target_localhost_port


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
