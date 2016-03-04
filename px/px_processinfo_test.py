import collections

import px_processinfo


def test_get_other_end_pids_basic():
    File = collections.namedtuple('File', ['name', 'plain_name', 'device', 'pid'])
    files = [File("name", "name", "0xPipeIdentifier", 25)]

    my_end = File("[] 0xPipeIdentifier", "0xPipeIdentifier", "whatever", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == [25]

    my_end = File("[] ->0xPipeIdentifier", "->0xPipeIdentifier", "whatever", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == [25]

    my_end = File("doesn't exist", "doesn't exist", "whatever", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == []


def test_get_other_end_pids_socket1():
    File = collections.namedtuple('File', ['name', 'plain_name', 'device', 'pid', 'access'])
    files = [File("[] /fifo/name", "/fifo/name", None, 25, "r")]

    my_end = File("[] /fifo/name", "/fifo/name", None, 42, "w")
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == [25]


def test_get_other_end_pids_socket2():
    File = collections.namedtuple('File', ['name', 'plain_name', 'device', 'pid', 'access'])
    files = [File("[] /fifo/name", "/fifo/name", None, 25, "w")]

    my_end = File("[] /fifo/name", "/fifo/name", None, 42, "r")
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == [25]
