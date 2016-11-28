import re
import os.path

from px import px_file
import testutils


def create_file(filetype, name, device, pid, access=None, inode=None):
    file = px_file.PxFile()
    file.type = filetype

    # Remove leading [] group from name if any
    file.name = re.match('(\[[^]]*\] )?(.*)', name).group(2)

    file.pid = pid
    file.device = device
    file.access = access
    file.inode = inode
    return file


def get_other_end_pids(my_file, all_files):
    """Wrapper around IpcMap._get_other_end_pids() so that we can test it"""
    return testutils.create_ipc_map(my_file.pid, all_files)._get_other_end_pids(my_file)


def test_get_other_end_pids_basic():
    PIPE_ID = '0x919E1D'
    files = [create_file("PIPE", "name", PIPE_ID, 25)]

    my_end = create_file("PIPE", "[] " + PIPE_ID, "0x1234", 42)
    found = get_other_end_pids(my_end, files)
    assert found == set([25])

    my_end = create_file("PIPE", "[] ->" + PIPE_ID, "0x1234", 42)
    found = get_other_end_pids(my_end, files)
    assert found == set([25])

    my_end = create_file("PIPE", "doesn't exist", "0x1234", 42)
    found = get_other_end_pids(my_end, files)
    assert found == set([])


def test_get_other_end_pids_osx_pipe1():
    files = [
        create_file("PIPE", "[] ->0xAda", "0xE0e", 25),
        create_file("PIPE", "[] ->0x59aee", "0xE0e", 26),
    ]
    my_end = create_file("PIPE", "[] ->0xE0e", "0x8000", 42)
    found = get_other_end_pids(my_end, files)
    assert found == set([25, 26])


def test_get_other_end_pids_osx_pipe2():
    files = [
        create_file("PIPE", "[] ->0xAda", "0xE0e", 25),
        create_file("PIPE", "[] ->0xAda", "0x38ee", 26),
    ]
    my_end = create_file("PIPE", "[] ->0x8a8de9", "0xAda", 42)
    found = get_other_end_pids(my_end, files)
    assert found == set([25, 26])


def test_get_other_end_pids_linux_pipe():
    files = [
        create_file("FIFO", "pipe", None, 100, inode="100200", access="r"),
        create_file("FIFO", "pipe", None, 200, inode="100200", access="w"),
        create_file("FIFO", "pipe", None, 300, inode="100300", access="w"),
    ]
    assert get_other_end_pids(files[0], files) == set([200])
    assert get_other_end_pids(files[1], files) == set([100])
    assert get_other_end_pids(files[2], files) == set()


def test_get_other_end_pids_fifo1():
    files = [create_file("FIFO", "[] /fifo/name", None, 25, "r")]

    my_end = create_file("FIFO", "[] /fifo/name", None, 42, "w")
    found = get_other_end_pids(my_end, files)
    assert found == set([25])


def test_get_other_end_pids_fifo2():
    files = [create_file("FIFO", "[] /fifo/name", None, 25, "w")]

    my_end = create_file("FIFO", "[] /fifo/name", None, 42, "r")
    found = get_other_end_pids(my_end, files)
    assert found == set([25])


def test_get_other_end_pids_linux_socket():
    files = [
        create_file("unix", "[] socket", "0xabc123", 25, "u"),
        create_file("unix", "[] socket", "0xabc123", 26, "u"),
        create_file("unix", "[] socket", "0xdef456", 27, "u"),
    ]

    my_end = create_file("unix", "[] socket", "0xabc123", 42, "u")
    found = get_other_end_pids(my_end, files)
    assert found == {25, 26}

    # Should get all PIDs including our own
    my_end.pid = 25
    found = get_other_end_pids(my_end, files)
    assert found == {25, 26}


def test_get_other_end_pids_osx_socket():
    """This is from a real world example"""
    atom_file = create_file("unix", "->0xebb7d964ac3da0b7", "0xebb7d964c20e6947", 1234, "u")
    python_file = create_file("unix", "->0xebb7d964c20e6947", "0xebb7d964ac3da0b7", 4567, "u")
    files = [atom_file, python_file]

    assert 4567 in get_other_end_pids(atom_file, files)
    assert 1234 in get_other_end_pids(python_file, files)


def test_get_other_end_pids_localhost_socket():
    # Real world test data
    tc_file = create_file(
        "IPv4", "localhost:33815->localhost:postgresql", "444139298", 33019, "u")
    postgres_file = create_file(
        "IPv4", "localhost:postgresql->localhost:33815", "444206166", 42745, "u")
    files = [tc_file, postgres_file]

    tc_ipc_map = testutils.create_ipc_map(33019, files)
    assert 42745 in tc_ipc_map._get_other_end_pids(tc_file)
    assert tc_file not in tc_ipc_map.network_connections

    postgres_ipc_map = testutils.create_ipc_map(42745, files)
    assert 33019 in postgres_ipc_map._get_other_end_pids(postgres_file)
    assert postgres_file not in postgres_ipc_map.network_connections


def test_get_other_end_pids_localhost_socket_names():
    # lsof usually presents a number of different names for localhost, because
    # of different network interfaces and other reasons. Make sure we identify
    # those and treat them like localhost.
    tc_file = create_file(
        "IPv4", "127.0.0.42:33815->localhost:postgresql", "444139298", 33019, "u")
    postgres_file = create_file(
        "IPv4", "localhost:postgresql->127.0.0.42:33815", "444206166", 42745, "u")
    files = [tc_file, postgres_file]

    tc_ipc_map = testutils.create_ipc_map(33019, files)
    assert 42745 in tc_ipc_map._get_other_end_pids(tc_file)
    assert tc_file not in tc_ipc_map.network_connections

    postgres_ipc_map = testutils.create_ipc_map(42745, files)
    assert 33019 in postgres_ipc_map._get_other_end_pids(postgres_file)
    assert postgres_file not in postgres_ipc_map.network_connections


def test_get_ipc_map_1():
    """Tyre kick IpcMap with some real world data"""
    files = None
    my_dir = os.path.dirname(__file__)
    with open(os.path.join(my_dir, "lsof-test-output-linux-1.txt"), "r") as lsof_output:
        files = px_file.lsof_to_files(lsof_output.read())

    ipc_map = testutils.create_ipc_map(1997, files)
    keys = list(ipc_map.keys())
    assert len(keys) == 2

    peer0 = keys[0]
    assert len(ipc_map[peer0]) == 1

    peer1 = keys[1]
    assert len(ipc_map[peer1]) == 1


def test_get_ipc_map_2():
    """Tyre kick IpcMap with some real world data"""
    files = None
    my_dir = os.path.dirname(__file__)
    with open(os.path.join(my_dir, "lsof-test-output-linux-2.txt"), "r") as lsof_output:
        files = px_file.lsof_to_files(lsof_output.read())

    ipc_map = testutils.create_ipc_map(777, files)
    keys = list(ipc_map.keys())
    assert len(keys) == 1

    peer0 = keys[0]
    assert len(ipc_map[peer0]) == 4
