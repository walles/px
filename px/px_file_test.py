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
    assert files[0].device_number() is None
    assert files[0].type == "DIR"
    assert files[0].name == "/"
    assert str(files[0]) == "[DIR] /"

    assert files[1].pid == 123
    assert files[1].access == "r"
    assert files[1].device is None
    assert files[1].device_number() is None
    assert files[1].type == "REG"
    assert files[1].name == "contains\nnewline"
    assert str(files[1]) == "contains\nnewline"

    assert files[2].pid == 123
    assert files[2].access == "w"
    assert files[2].device == "0x42"
    assert files[2].device_number() == 0x42
    assert files[2].type == "REG"
    assert files[2].name == "/somefile"
    assert str(files[2]) == "/somefile"

    assert files[3].pid == 456
    assert files[3].access == "rw"
    assert files[3].device is None
    assert files[3].device_number() is None
    assert files[3].type == "REG"
    assert files[3].name == "/someotherfile"
    assert str(files[3]) == "/someotherfile"

    assert files[4].pid == 456
    assert files[4].access is None
    assert files[4].device is None
    assert files[4].device_number() is None
    assert files[4].type == "??"
    assert files[4].name == "(revoked)"
    assert str(files[4]) == "[??] (revoked)"


def test_get_all():
    files = px_file.get_all()

    # As non-root I get 6000 on my system, 100 should be fine anywhere. And if
    # not, we'll just have to document our finding and lower this value
    assert len(files) > 100


def lsof_to_file(shard_array):
    return px_file.lsof_to_files('\0'.join(shard_array + ["\n"]))[0]


def create_file(type, name):
    return lsof_to_file(["f6", "au", "t" + type, "d0x42", "n" + name])


def test_listen_name():
    file = lsof_to_file(["f6", "au", "tIPv4", "d0x42", "nlocalhost:63342"])
    assert file.name == "localhost:63342"
    assert str(file) == "[IPv4] localhost:63342 (LISTEN)"

    file = lsof_to_file(["f6", "au", "tIPv6", "d0x42", "nlocalhost:63342"])
    assert file.name == "localhost:63342"
    assert str(file) == "[IPv6] localhost:63342 (LISTEN)"


def test_setability():
    # Can files be stored in sets?
    a = lsof_to_file(["f6", "aw", "tREG", "d0x42", "n/somefile"])
    b = lsof_to_file(["f6", "aw", "tREG", "d0x42", "n/somefile"])
    s = set([a, b])
    assert len(s) == 1


def test_local_endpoint():
    local_endpoint = lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                                   "nlocalhost:postgres->localhost:33331"]).get_endpoints()[0]
    assert local_endpoint == "localhost:postgres"

    local_endpoint = lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                                   "nlocalhost:39252->localhost:39252"]).get_endpoints()[0]
    assert local_endpoint == "localhost:39252"

    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "nlocalhost:19091"]).get_endpoints()[0] == "localhost:19091"
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "nlocalhost:ipp (LISTEN)"]).get_endpoints()[0] == "localhost:ipp"

    # We can't match against endpoint address "*"
    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "n*:57919"]).get_endpoints()[0] is None
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:57919"]).get_endpoints()[0] is None

    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:*"]).get_endpoints()[0] is None
    assert lsof_to_file(["f6", "aw", "tREG", "d0x42",
                         "n/somefile"]).get_endpoints()[0] is None


def test_remote_endpoint():
    remote_endpoint = lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                                    "nlocalhost:postgresql->localhost:3331"]).get_endpoints()[1]
    assert remote_endpoint == "localhost:3331"

    remote_endpoint = lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                                    "nlocalhost:postgresql->otherhost:3331"]).get_endpoints()[1]
    assert remote_endpoint == "otherhost:3331"

    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "nlocalhost:19091"]).get_endpoints()[1] is None
    assert lsof_to_file(["f6", "au", "tIPv6", "d0x42",
                         "n*:57919"]).get_endpoints()[1] is None
    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:57919"]).get_endpoints()[1] is None

    assert lsof_to_file(["f6", "au", "tIPv4", "d0x42",
                         "n*:*"]).get_endpoints()[1] is None
    assert lsof_to_file(["f6", "aw", "tREG", "d0x42",
                         "n/somefile"]).get_endpoints()[1] is None
