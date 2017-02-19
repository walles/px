import os

from px import px_cpuinfo


def test_get_core_count():
    physical, logical = px_cpuinfo.get_core_count()

    assert physical >= 1
    assert logical >= physical
    assert logical % physical == 0


def test_get_core_count_from_proc_cpuinfo():
    my_dir = os.path.dirname(__file__)
    physical, logical = px_cpuinfo.get_core_count_from_proc_cpuinfo(
        os.path.join(my_dir, "proc-cpuinfo-sample"))

    assert physical == FIXME
    assert logical == FIXME

    assert px_cpuinfo.get_core_count_from_proc_cpuinfo("/does/not/exist") == None


def test_get_core_count_from_sysctl():
    test_me = px_cpuinfo.get_core_count_from_sysctl()
    if test_me is None:
        # We're likely on Linux
        return

    # Sanity check, since we don't know the answer this is the best we can do
    physical, logical = test_me
    assert physical >= 1
    assert logical >= physical
    assert logical % physical == 0
