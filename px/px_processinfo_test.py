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


def test_get_closests_starts_all_within_1s():
    # Verify that even if we have a large number of processes created within 1s
    # of the base one, we get all of those
    all = []
    all.append(testutils.create_process(pid=100, timestring="Mon Mar 7 09:33:09 2016"))
    all.append(testutils.create_process(pid=101, timestring="Mon Mar 7 09:33:10 2016"))
    all.append(testutils.create_process(pid=102, timestring="Mon Mar 7 09:33:10 2016"))
    all.append(testutils.create_process(pid=103, timestring="Mon Mar 7 09:33:10 2016"))
    all.append(testutils.create_process(pid=104, timestring="Mon Mar 7 09:33:11 2016"))

    base = testutils.create_process(pid=105, timestring="Mon Mar 7 09:33:11 2016")
    all.append(base)

    all.append(testutils.create_process(pid=106, timestring="Mon Mar 7 09:33:11 2016"))
    all.append(testutils.create_process(pid=107, timestring="Mon Mar 7 09:33:12 2016"))
    all.append(testutils.create_process(pid=108, timestring="Mon Mar 7 09:33:12 2016"))
    all.append(testutils.create_process(pid=109, timestring="Mon Mar 7 09:33:12 2016"))
    all.append(testutils.create_process(pid=110, timestring="Tue Mar 8 09:33:13 2016"))

    close = px_processinfo.get_closest_starts(base, all)
    assert len(close) == 8
    assert all[0] not in close
    assert all[1] in close
    assert all[2] in close
    assert all[3] in close
    assert all[4] in close
    assert all[5] not in close  # This is base, it shouldn't be close to itself
    assert all[6] in close
    assert all[7] in close
    assert all[8] in close
    assert all[9] in close
    assert all[10] not in close


def test_get_closest_starts_five_closest():
    # Verify that we list the five closest processes even if none of them are
    # very close
    all = []
    all.append(testutils.create_process(pid=102, timestring="Mon Mar 7 06:33:10 2016"))
    all.append(testutils.create_process(pid=103, timestring="Mon Mar 7 07:33:10 2016"))
    all.append(testutils.create_process(pid=104, timestring="Mon Mar 7 08:33:11 2016"))

    base = testutils.create_process(pid=105, timestring="Mon Mar 7 09:33:11 2016")
    all.append(base)

    all.append(testutils.create_process(pid=106, timestring="Mon Mar 7 10:33:11 2016"))
    all.append(testutils.create_process(pid=107, timestring="Mon Mar 7 11:33:12 2016"))
    all.append(testutils.create_process(pid=108, timestring="Mon Mar 7 11:43:12 2016"))
    all.append(testutils.create_process(pid=110, timestring="Tue Mar 7 12:33:13 2016"))

    close = px_processinfo.get_closest_starts(base, all)
    assert len(close) == 5
    assert all[0] not in close
    assert all[1] in close
    assert all[2] in close
    assert all[3] not in close  # This is base, it shouldn't be close to itself
    assert all[4] in close
    assert all[5] in close
    assert all[6] in close
    assert all[7] not in close
