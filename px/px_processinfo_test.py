import re
import px_file
import testutils
import px_processinfo


def create_file(name, device, pid, access=None):
    file = px_file.PxFile()
    file.name = name

    # Remove leading [] group from name if any
    file.plain_name = re.match('(\[[^]]*\] )?(.*)', name).group(2)

    file.pid = pid
    file.access = access
    file.device = device
    return file


def test_get_other_end_pids_basic():
    files = [create_file("name", "0xPipeIdentifier", 25)]

    my_end = create_file("[] 0xPipeIdentifier", "whatever", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == set([25])

    my_end = create_file("[] ->0xPipeIdentifier", "whatever", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == set([25])

    my_end = create_file("doesn't exist", "whatever", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == set([])


def test_get_other_end_pids_osx_pipe1():
    files = [
        create_file("[] ->0xAdam", "0xEve", 25),
        create_file("[] ->0xSnake", "0xEve", 26),
    ]
    my_end = create_file("[] ->0xEve", "0xBook", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == set([25, 26])


def test_get_other_end_pids_osx_pipe2():
    files = [
        create_file("[] ->0xAdam", "0xEve", 25),
        create_file("[] ->0xAdam", "0xTree", 26),
    ]
    my_end = create_file("[] ->0xGarden", "0xAdam", 42)
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == set([25, 26])


def test_get_other_end_pids_fifo1():
    files = [create_file("[] /fifo/name", None, 25, "r")]

    my_end = create_file("[] /fifo/name", None, 42, "w")
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == set([25])


def test_get_other_end_pids_fifo2():
    files = [create_file("[] /fifo/name", None, 25, "w")]

    my_end = create_file("[] /fifo/name", None, 42, "r")
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == set([25])


def test_get_other_end_pids_linux_socket():
    files = [
        create_file("[] socket", "0xabc123", 25, "u"),
        create_file("[] socket", "0xabc123", 26, "u"),
        create_file("[] socket", "0xdef456", 27, "u"),
    ]

    my_end = create_file("[] socket", "0xabc123", 42, "u")
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == {25, 26}

    # Should get all PIDs including our own
    my_end.pid = 25
    found = px_processinfo.get_other_end_pids(my_end, files)
    assert found == {25, 26}


def test_to_relative_start_string():
    base = testutils.create_process(pid=100, timestring="Mon Mar 7 09:33:11 2016")
    close = testutils.create_process(pid=101, timestring="Mon Mar 7 09:33:12 2016")
    assert ("cupsd(101) was started 1.0s after cupsd(100)" ==
            px_processinfo.to_relative_start_string(base, close))

    base = testutils.create_process(pid=100, timestring="Mon Mar 7 09:33:11 2016")
    close = testutils.create_process(pid=101, timestring="Mon Mar 7 09:33:10 2016")
    assert ("cupsd(101) was started 1.0s before cupsd(100)" ==
            px_processinfo.to_relative_start_string(base, close))

    base = testutils.create_process(pid=100, timestring="Mon Mar 7 09:33:11 2016")
    close = testutils.create_process(pid=101, timestring="Mon Mar 7 09:33:11 2016")
    assert ("cupsd(101) was started just after cupsd(100)" ==
            px_processinfo.to_relative_start_string(base, close))
