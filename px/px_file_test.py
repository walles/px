import px_file


def test_lsof_to_files():
    lsof = ""

    lsof += '\0'.join(["p123", "\n"])
    lsof += '\0'.join(["fcwd", "a ", "tDIR", "n/", "\n"])
    lsof += '\0'.join(["f5", "ar", "tREG", "ncontains\nnewline", "\n"])
    lsof += '\0'.join(["f6", "aw", "tREG", "d0x42", "n/somefile", "\n"])
    lsof += '\0'.join(["p456", "\n"])
    lsof += '\0'.join(["f7", "au", "tREG", "n/someotherfile", "\n"])
    lsof += '\0'.join(["f7", "a ", "n(revoked)", "\n"])

    files = px_file.lsof_to_files(lsof)

    assert len(files) == 5

    assert files[0].pid == 123
    assert files[0].access is None
    assert files[0].device is None
    assert files[0].device_number is None
    assert files[0].type == "DIR"
    assert files[0].name == "[DIR] /"
    assert files[0].plain_name == "/"

    assert files[1].pid == 123
    assert files[1].access == "r"
    assert files[1].device is None
    assert files[1].device_number is None
    assert files[1].type == "REG"
    assert files[1].name == "contains\nnewline"
    assert files[1].plain_name == "contains\nnewline"

    assert files[2].pid == 123
    assert files[2].access == "w"
    assert files[2].device == "0x42"
    assert files[2].device_number == 0x42
    assert files[2].type == "REG"
    assert files[2].name == "/somefile"
    assert files[2].plain_name == "/somefile"

    assert files[3].pid == 456
    assert files[3].access == "rw"
    assert files[3].device is None
    assert files[3].device_number is None
    assert files[3].type == "REG"
    assert files[3].name == "/someotherfile"
    assert files[3].plain_name == "/someotherfile"

    assert files[4].pid == 456
    assert files[4].access is None
    assert files[4].device is None
    assert files[4].device_number is None
    assert files[4].type == "??"
    assert files[4].name == "[??] (revoked)"
    assert files[4].plain_name == "(revoked)"


def test_get_all():
    files = px_file.get_all()

    # As non-root I get 6000 on my system, 100 should be fine anywhere. And if
    # not, we'll just have to document our finding and lower this value
    assert len(files) > 100


def lsof_to_file(shard_array):
    return px_file.lsof_to_files('\0'.join(shard_array + ["\n"]))[0]


def test_setability():
    # Can files be stored in sets?
    a = lsof_to_file(["f6", "aw", "tREG", "d0x42", "n/somefile"])
    b = lsof_to_file(["f6", "aw", "tREG", "d0x42", "n/somefile"])
    s = set([a, b])
    assert len(s) == 1


def test_localhost_port():
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "nlocalhost:postgresql->localhost:33331"]).localhost_port == "postgresql"
    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "nlocalhost:39252->localhost:39252"]).localhost_port == "39252"
    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "nlocalhost:19091"]).localhost_port == "19091"
    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "n*:57919"]).localhost_port == "57919"
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:57919"]).localhost_port == "57919"
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "nlocalhost:ipp (LISTEN)"]).localhost_port == "ipp"

    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:*"]).localhost_port is None
    assert lsof_to_file(["f6", "aw", "tREG", "d0x42",
                         "n/somefile"]).localhost_port is None


def test_target_localhost_port():
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "nlocalhost:postgresql->localhost:3331"]).target_localhost_port == "3331"
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "nlocalhost:postgresql->otherhost:3331"]).target_localhost_port is None

    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "nlocalhost:19091"]).target_localhost_port is None
    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "n*:57919"]).target_localhost_port is None
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:57919"]).target_localhost_port is None

    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:*"]).target_localhost_port is None
    assert lsof_to_file(["f6", "aw", "tREG", "d0x42",
                         "n/somefile"]).target_localhost_port is None
