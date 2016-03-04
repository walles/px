import collections

import px_processinfo


def test_get_other_end_pid_basic():
    File = collections.namedtuple('File', ['name', 'device', 'pid'])
    files = [File("name", "0xPipeIdentifier", 25)]

    found = px_processinfo.get_other_end_pid("0xPipeIdentifier", files)
    assert found == 25

    found = px_processinfo.get_other_end_pid("doesn't exist", files)
    assert found is None
