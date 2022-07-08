import os.path

from px import px_file
from px import px_ipc_map
from . import testutils


def get_other_end_pids(my_file, all_files):
    """Wrapper around IpcMap._get_other_end_pids() so that we can test it"""
    return testutils.create_ipc_map(my_file.pid, all_files)._get_other_end_pids(my_file)


def test_get_other_end_pids_basic():
    PIPE_ID = "0x919E1D"
    files = [testutils.create_file("PIPE", "name", PIPE_ID, 25)]

    my_end = testutils.create_file("PIPE", "[] " + PIPE_ID, "0x1234", 42)
    found = get_other_end_pids(my_end, files)
    assert found == {25}

    my_end = testutils.create_file("PIPE", "[] ->" + PIPE_ID, "0x1234", 42)
    found = get_other_end_pids(my_end, files)
    assert found == {25}

    my_end = testutils.create_file("PIPE", "doesn't exist", "0x1234", 42)
    found = get_other_end_pids(my_end, files)
    assert found == set()


def test_get_other_end_pids_osx_pipe1():
    files = [
        testutils.create_file("PIPE", "[] ->0xAda", "0xE0e", 25),
        testutils.create_file("PIPE", "[] ->0x59aee", "0xE0e", 26),
    ]
    my_end = testutils.create_file("PIPE", "[] ->0xE0e", "0x8000", 42)
    found = get_other_end_pids(my_end, files)
    assert found == {25, 26}


def test_get_other_end_pids_osx_pipe2():
    files = [
        testutils.create_file("PIPE", "[] ->0xAda", "0xE0e", 25),
        testutils.create_file("PIPE", "[] ->0xAda", "0x38ee", 26),
    ]
    my_end = testutils.create_file("PIPE", "[] ->0x8a8de9", "0xAda", 42)
    found = get_other_end_pids(my_end, files)
    assert found == {25, 26}


def test_get_other_end_pids_linux_pipe():
    files = [
        testutils.create_file("FIFO", "pipe", None, 100, inode="100200", access="r"),
        testutils.create_file("FIFO", "pipe", None, 200, inode="100200", access="w"),
        testutils.create_file("FIFO", "pipe", None, 300, inode="100300", access="w"),
    ]
    assert get_other_end_pids(files[0], files) == {200}
    assert get_other_end_pids(files[1], files) == {100}
    assert get_other_end_pids(files[2], files) == set()


def test_get_other_end_pids_fifo1():
    files = [testutils.create_file("FIFO", "[] /fifo/name", None, 25, "r")]

    my_end = testutils.create_file("FIFO", "[] /fifo/name", None, 42, "w")
    found = get_other_end_pids(my_end, files)
    assert found == {25}


def test_get_other_end_pids_fifo2():
    files = [testutils.create_file("FIFO", "[] /fifo/name", None, 25, "w")]

    my_end = testutils.create_file("FIFO", "[] /fifo/name", None, 42, "r")
    found = get_other_end_pids(my_end, files)
    assert found == {25}


def test_get_other_end_pids_linux_socket():
    files = [
        testutils.create_file("unix", "[] socket", "0xabc123", 25, "u"),
        testutils.create_file("unix", "[] socket", "0xabc123", 26, "u"),
        testutils.create_file("unix", "[] socket", "0xdef456", 27, "u"),
    ]

    my_end = testutils.create_file("unix", "[] socket", "0xabc123", 42, "u")
    found = get_other_end_pids(my_end, files)
    assert found == {25, 26}

    # Should get all PIDs including our own
    my_end.pid = 25
    found = get_other_end_pids(my_end, files)
    assert found == {25, 26}


def test_get_other_end_pids_osx_socket():
    """This is from a real world example"""
    atom_file = testutils.create_file(
        "unix", "->0xebb7d964ac3da0b7", "0xebb7d964c20e6947", 1234, "u"
    )
    python_file = testutils.create_file(
        "unix", "->0xebb7d964c20e6947", "0xebb7d964ac3da0b7", 4567, "u"
    )
    files = [atom_file, python_file]

    assert 4567 in get_other_end_pids(atom_file, files)
    assert 1234 in get_other_end_pids(python_file, files)


def test_get_other_end_pids_localhost_socket():
    # Real world test data
    tc_file = testutils.create_file(
        "IPv4", "localhost:33815->localhost:postgresql", "444139298", 33019, "u"
    )
    postgres_file = testutils.create_file(
        "IPv4", "localhost:postgresql->localhost:33815", "444206166", 42745, "u"
    )
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
    tc_file = testutils.create_file(
        "IPv4", "127.0.0.42:33815->localhost:postgresql", "444139298", 33019, "u"
    )
    postgres_file = testutils.create_file(
        "IPv4", "localhost:postgresql->127.0.0.42:33815", "444206166", 42745, "u"
    )
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
    with open(
        os.path.join(my_dir, "lsof-test-output-linux-1.txt"), encoding="utf-8"
    ) as lsof_output:
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
    with open(
        os.path.join(my_dir, "lsof-test-output-linux-2.txt"), encoding="utf-8"
    ) as lsof_output:
        files = px_file.lsof_to_files(lsof_output.read())

    ipc_map = testutils.create_ipc_map(777, files)
    keys = list(ipc_map.keys())
    assert len(keys) == 1

    peer0 = keys[0]
    assert len(ipc_map[peer0]) == 4


def test_stdfds_base():
    files = [
        testutils.create_file("REG", "/wherever/stdin", None, 1234, fd=0),
        testutils.create_file("REG", "/wherever/stdout", None, 1234, fd=1),
        testutils.create_file("REG", "/wherever/stderr", None, 1234, fd=2),
    ]

    ipc_map = testutils.create_ipc_map(1234, files)
    assert ipc_map.fds[0] == "/wherever/stdin"
    assert ipc_map.fds[1] == "/wherever/stdout"
    assert ipc_map.fds[2] == "/wherever/stderr"


def test_stdfds_closed():
    files = [
        testutils.create_file("REG", "/wherever", None, 1234, fd=3),
    ]

    ipc_map = testutils.create_ipc_map(1234, files)

    # If we get other fds but not 0-2, we assume 0-2 to have been closed.
    assert ipc_map.fds[0] == "<closed>"
    assert ipc_map.fds[1] == "<closed>"
    assert ipc_map.fds[2] == "<closed>"


def test_stdfds_unavailable():
    ipc_map = testutils.create_ipc_map(1234, [])

    # If we get no fds at all for this process, we assume lack of data
    assert ipc_map.fds[0] == "<unavailable, running px as root might help>"
    assert ipc_map.fds[1] == "<unavailable, running px as root might help>"
    assert ipc_map.fds[2] == "<unavailable, running px as root might help>"


def test_stdfds_ipc_and_network():
    files = [
        # Set up stdin to do a network connection to another local process
        testutils.create_file(
            "IPv4",
            "localhost:33815->localhost:postgresql",
            "444139298",
            1234,
            "u",
            fd=0,
        ),
        testutils.create_file(
            "IPv4", "localhost:postgresql->localhost:33815", "444206166", 1000, "u"
        ),
        # Set up stdout to do a network connection to 8.8.8.8
        testutils.create_file(
            "IPv4", "127.0.0.1:9999->8.8.8.8:https", None, 1234, fd=1
        ),
        # Set up stderr to pipe to another process. Pipes are real-world OS X ones.
        testutils.create_file(
            "PIPE", "->0x3922f6866312c495", "0x3922f6866312cb55", 1234, fd=2
        ),
        testutils.create_file(
            "PIPE", "->0x3922f6866312cb55", "0x3922f6866312c495", 1002
        ),
    ]

    ipc_map = testutils.create_ipc_map(1234, files)
    assert (
        ipc_map.fds[0]
        == "[IPv4] -> cupsd(1000) (localhost:33815->localhost:postgresql)"
    )
    assert ipc_map.fds[1] in [
        "[IPv4] localhost:9999->google-public-dns-a.google.com:https",
        "[IPv4] localhost:9999->dns.google:https",
    ]
    assert ipc_map.fds[2] == "[PIPE] -> cupsd(1002) (0x3922f6866312c495)"


def test_stdfds_pipe_to_unknown_not_root():
    files = [
        # Set up stderr as an unconnected pipe. The pipes is a real-world OS X one.
        testutils.create_file(
            "PIPE", "->0x3922f6866312c495", "0x3922f6866312cb55", 1234, fd=2
        ),
    ]

    ipc_map = testutils.create_ipc_map(1234, files, is_root=False)
    assert (
        ipc_map.fds[2]
        == "[PIPE] <destination not found, try running px as root> (0x3922f6866312c495)"
    )


def test_stdfds_pipe_to_unknown_is_root():
    files = [
        # Set up stderr as an unconnected pipe. The pipe is a real-world OS X one.
        testutils.create_file(
            "PIPE", "->0x3922f6866312c495", "0x3922f6866312cb55", 1234, fd=2
        ),
    ]

    ipc_map = testutils.create_ipc_map(1234, files, is_root=True)
    assert ipc_map.fds[2] == "[PIPE] <not connected> (0x3922f6866312c495)"


def test_stdfds_osx_pipe_to_unknown_is_root():
    files = [
        # Set up stdin as an unconnected pipe. The pipe is a real-world OS X one.
        testutils.create_file("PIPE", "", "0x3922f6866312cb55", 1234, fd=0),
    ]

    ipc_map = testutils.create_ipc_map(1234, files, is_root=True)
    assert ipc_map.fds[0] == "[PIPE] <not connected> (0x3922f6866312cb55)"


def test_ipc_pipe_osx():
    # These pipes are real-world OS X ones
    f1 = testutils.create_file(
        "PIPE", "->0x3922f6866312c495", "0x3922f6866312cb55", 2222
    )
    assert f1.fifo_id() == "->0x3922f6866312c495"

    f2 = testutils.create_file(
        "PIPE", "->0x3922f6866312cb55", "0x3922f6866312c495", 1001
    )
    assert f2.fifo_id() == "->0x3922f6866312cb55"

    files = [f1, f2]

    ipc_map = testutils.create_ipc_map(2222, files)
    assert 1001 in ipc_map._get_other_end_pids(f1)
    assert 2222 in ipc_map._get_other_end_pids(f2)
    assert len(list(ipc_map.keys())) == 1


def test_peer_process_str():
    assert str(px_ipc_map.PeerProcess(pid=45)) == "PID 45"
    assert str(px_ipc_map.PeerProcess(name="Johan")) == "Johan"
