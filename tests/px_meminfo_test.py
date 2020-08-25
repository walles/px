import os

from px import px_meminfo

def test_get_ram_numbers_from_proc_none():
    my_dir = os.path.dirname(__file__)

    info = px_meminfo._get_ram_numbers_from_proc(
        os.path.join(my_dir, "file name that doesn't exist"))
    assert info is None


def test_get_ram_numbers_from_proc_2010():
    my_dir = os.path.dirname(__file__)

    info = px_meminfo._get_ram_numbers_from_proc(
        os.path.join(my_dir, "proc-meminfo-2010.txt"))
    assert info is not None

    total_bytes, wanted_bytes = info
    assert total_bytes == 1921988 * 1024

    # From before MemAvailable's invention:
    # https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=34e431b0ae398fc54ea69ff85ec700722c9da773
    available_kb = 1374408 + 32688 + 370540 + 0
    assert wanted_bytes == total_bytes - available_kb * 1024


def test_get_ram_numbers_from_proc_2020():
    my_dir = os.path.dirname(__file__)

    info = px_meminfo._get_ram_numbers_from_proc(
        os.path.join(my_dir, "proc-meminfo-2020.txt"))
    assert info is not None

    total_bytes, wanted_bytes = info
    assert total_bytes == 371474308 * 1024

    # Use MemAvailable when available:
    # https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/commit/?id=34e431b0ae398fc54ea69ff85ec700722c9da773
    available_kb = 294625460
    assert wanted_bytes == total_bytes - available_kb * 1024


def test_bytes_to_string():
    assert px_meminfo.bytes_to_string(1024*7 - 1) == "7167B"
    assert px_meminfo.bytes_to_string(1024*7) == "7KB"

    assert px_meminfo.bytes_to_string((1024 ** 2)*7 - 1) == "7167KB"
    assert px_meminfo.bytes_to_string((1024 ** 2)*7) == "7MB"

    assert px_meminfo.bytes_to_string((1024 ** 3)*7 - 1) == "7167MB"
    assert px_meminfo.bytes_to_string((1024 ** 3)*7) == "7TB"

    assert px_meminfo.bytes_to_string((1024 ** 4)*10) == "10000TB"
