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
