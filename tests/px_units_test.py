from px import px_units


def test_bytes_to_string():
    assert px_units.bytes_to_string(1024 * 7 - 1) == "7167B"
    assert px_units.bytes_to_string(1024 * 7) == "7KB"

    assert px_units.bytes_to_string((1024 ** 2) * 7 - 1) == "7168KB"
    assert px_units.bytes_to_string((1024 ** 2) * 7) == "7MB"

    assert px_units.bytes_to_string((1024 ** 3) * 7 - 1) == "7168MB"
    assert px_units.bytes_to_string((1024 ** 3) * 7) == "7GB"

    assert px_units.bytes_to_string((1024 ** 4) * 7 - 1) == "7168GB"
    assert px_units.bytes_to_string((1024 ** 4) * 7) == "7TB"

    assert px_units.bytes_to_string((1024 ** 5) * 10) == "10240TB"
