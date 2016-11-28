from px import px_process
from px import px_processinfo

import testutils


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


def test_print_starttime():
    # Just make sure it doesn't crash
    all = px_process.get_all()
    process0 = list(filter(lambda p: p.pid == 0, all))[0]
    px_processinfo.print_start_time(process0)


def test_print_process_subtree():
    lines = []

    child_proc = testutils.create_process(pid=2, commandline="child")
    child_proc.children = []

    parent_proc = testutils.create_process(pid=1, commandline="parent")
    parent_proc.children = [child_proc]

    px_processinfo.print_process_subtree(parent_proc, 0, lines)

    assert lines == [
        ('' + str(parent_proc), parent_proc),
        ('  ' + str(child_proc), child_proc)
    ]
