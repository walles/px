from px import px_launchcounter

from . import testutils


def test_list_new_launches():
    process = \
        testutils.create_process(pid=100, timestring="Mon Apr 7 09:33:11 2010")
    process_identical = \
        testutils.create_process(pid=100, timestring="Mon Apr 7 09:33:11 2010")
    process_other_pid = \
        testutils.create_process(pid=101, timestring="Mon Apr 7 09:33:11 2010")
    process_other_starttime = \
        testutils.create_process(pid=100, timestring="Mon Apr 8 09:33:11 2010")

    before = [process]
    after = [process_identical, process_other_pid, process_other_starttime]

    new_processes = px_launchcounter.Launchcounter()._list_new_launches(before, after)

    # We should get unicode responses from getch()
    assert new_processes == [process_other_pid, process_other_starttime]
