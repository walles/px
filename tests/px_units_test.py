from px import px_units


def test_bytes_to_strings():
    assert px_units.bytes_to_strings(0, 1024 * 7 - 1) == ("0B", "7167B")
    assert px_units.bytes_to_strings(0, 1024 * 7) == ("0KB", "7KB")

    assert px_units.bytes_to_strings(0, (1024**2) * 7 - 1) == ("0KB", "7168KB")
    assert px_units.bytes_to_strings(0, (1024**2) * 7) == ("0MB", "7MB")

    assert px_units.bytes_to_strings(0, (1024**3) * 7 - 1) == ("0MB", "7168MB")
    assert px_units.bytes_to_strings(0, (1024**3) * 7) == ("0GB", "7GB")

    assert px_units.bytes_to_strings(0, (1024**4) * 7 - 1) == ("0GB", "7168GB")
    assert px_units.bytes_to_strings(0, (1024**4) * 7) == ("0TB", "7TB")

    assert px_units.bytes_to_strings(0, (1024**5) * 10) == ("0TB", "10240TB")
