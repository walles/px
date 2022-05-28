import os

from px import px_cpuinfo


def test_get_core_count():
    physical, logical = px_cpuinfo.get_core_count()

    assert physical >= 1
    assert logical >= physical
    assert logical % physical == 0


def assert_core_counts_from_file(filename, expected_physical, expected_logical):
    my_dir = os.path.dirname(__file__)

    info = px_cpuinfo.get_core_count_from_proc_cpuinfo(os.path.join(my_dir, filename))
    assert info
    physical, logical = info
    assert physical == expected_physical
    assert logical == expected_logical


def test_get_core_count_from_proc_cpuinfo():
    assert_core_counts_from_file("proc-cpuinfo-1p1l.txt", 1, 1)
    assert_core_counts_from_file("proc-cpuinfo-2p4l.txt", 2, 4)
    assert_core_counts_from_file("proc-cpuinfo-24p96l.txt", 24, 96)

    # This one is from my cell phone, just to provide a weird corner case example of things
    # we may have to handle.
    assert_core_counts_from_file("proc-cpuinfo-8p8l.txt", 8, 8)

    assert px_cpuinfo.get_core_count_from_proc_cpuinfo("/does/not/exist") is None


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


def test_parse_sysctl_output():
    result = px_cpuinfo.parse_sysctl_output([])
    assert result == (None, None)

    result = px_cpuinfo.parse_sysctl_output(["gurka"])
    assert result == (None, None)

    result = px_cpuinfo.parse_sysctl_output(["hw.physicalcpu: 1", "hw.logicalcpu: 2"])
    assert result == (1, 2)

    result = px_cpuinfo.parse_sysctl_output(["hw.physicalcpu: 12", "hw.logicalcpu: 34"])
    assert result == (12, 34)
