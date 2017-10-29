# coding: utf-8

import os
import re
import six

from px import px_file

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List      # NOQA


def test_lsof_to_files():
    lsof = b""

    lsof += b'\0'.join([b"p123", b"\n"])
    lsof += b'\0'.join([b"fcwd", b"a ", b"tDIR", b"n/", b"\n"])
    lsof += b'\0'.join([b"f5", b"ar", b"tREG", b"ncontains\nnewline", b"\n"])
    lsof += b'\0'.join([b"f6", b"aw", b"tREG", b"d0x42", b"n/somefile", b"\n"])
    lsof += b'\0'.join([b"p456", b"\n"])
    lsof += b'\0'.join([b"f7", b"au", b"tREG", b"n/someotherfile", b"\n"])
    lsof += b'\0'.join([b"f7", b"a ", b"n(revoked)", b"\n"])

    files = px_file.lsof_to_files(lsof, None, None)

    assert len(files) == 5

    assert files[0].pid == 123
    assert files[0].access is None
    assert files[0].device is None
    assert files[0].device_number() is None
    assert files[0].type == u"DIR"
    assert files[0].name == u"/"
    assert str(files[0]) == u"[DIR] /"

    assert files[1].pid == 123
    assert files[1].access == u"r"
    assert files[1].device is None
    assert files[1].device_number() is None
    assert files[1].type == u"REG"
    assert files[1].name == u"contains\nnewline"
    assert str(files[1]) == u"contains\nnewline"

    assert files[2].pid == 123
    assert files[2].access == u"w"
    assert files[2].device == u"0x42"
    assert files[2].device_number() == 0x42
    assert files[2].type == u"REG"
    assert files[2].name == u"/somefile"
    assert str(files[2]) == u"/somefile"

    assert files[3].pid == 456
    assert files[3].access == u"rw"
    assert files[3].device is None
    assert files[3].device_number() is None
    assert files[3].type == u"REG"
    assert files[3].name == u"/someotherfile"
    assert str(files[3]) == u"/someotherfile"

    assert files[4].pid == 456
    assert files[4].access is None
    assert files[4].device is None
    assert files[4].device_number() is None
    assert files[4].type == u"??"
    assert files[4].name == u"(revoked)"
    assert str(files[4]) == u"[??] (revoked)"


def test_get_all(tmpdir):
    utf8filename = os.path.join(tmpdir, u"😀-xmarker")
    open(utf8filename, 'w').close()
    assert os.path.isfile(utf8filename)

    with open(utf8filename, "r"):
        files = px_file.get_all(None)

    # As non-root I get 6000 on my system, 100 should be fine anywhere. And if
    # not, we'll just have to document our finding and lower this value
    assert len(files) > 100

    found_it = False
    for file in files:
        assert type(file.name) == six.text_type
        assert type(file.describe()) == six.text_type
        if u"xmarker" in file.name:
            # Help debug unicode problems
            print(file.name)
        if file.name == utf8filename:
            found_it = True

    assert found_it


def lsof_to_file(shard_array):
    # type: (List[bytes]) -> px_file.PxFile
    return px_file.lsof_to_files(b'\0'.join(shard_array + [b"\n"]), None, None)[0]


def test_listen_name():
    file = lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42", b"nlocalhost:63342"])
    assert file.name == u"localhost:63342"
    assert str(file) == u"[IPv4] localhost:63342 (LISTEN)"

    file = lsof_to_file([b"f6", b"au", b"tIPv6", b"d0x42", b"nlocalhost:63342"])
    assert file.name == u"localhost:63342"
    assert str(file) == u"[IPv6] localhost:63342 (LISTEN)"


def test_setability():
    # Can files be stored in sets?
    a = lsof_to_file([b"f6", b"aw", b"tREG", b"d0x42", b"n/somefile"])
    b = lsof_to_file([b"f6", b"aw", b"tREG", b"d0x42", b"n/somefile"])
    s = set([a, b])
    assert len(s) == 1


def test_local_endpoint():
    local_endpoint = lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                                   b"nlocalhost:postgres->localhost:33331"]).get_endpoints()[0]
    assert local_endpoint == "localhost:postgres"

    local_endpoint = lsof_to_file([b"f6", b"au", b"tIPv6", b"d0x42",
                                   b"nlocalhost:39252->localhost:39252"]).get_endpoints()[0]
    assert local_endpoint == "localhost:39252"

    assert lsof_to_file([b"f6", b"au", b"tIPv6", b"d0x42",
                         b"nlocalhost:19091"]).get_endpoints()[0] == "localhost:19091"
    assert lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                         b"nlocalhost:ipp (LISTEN)"]).get_endpoints()[0] == "localhost:ipp"

    # We can't match against endpoint address "*"
    assert lsof_to_file([b"f6", b"au", b"tIPv6", b"d0x42",
                         b"n*:57919"]).get_endpoints()[0] is None
    assert lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                         b"n*:57919"]).get_endpoints()[0] is None

    assert lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                         b"n*:*"]).get_endpoints()[0] is None
    assert lsof_to_file([b"f6", b"aw", b"tREG", b"d0x42",
                         b"n/somefile"]).get_endpoints()[0] is None


def test_remote_endpoint():
    remote_endpoint = lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                                    b"nlocalhost:postgresql->localhost:3331"]).get_endpoints()[1]
    assert remote_endpoint == "localhost:3331"

    remote_endpoint = lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                                    b"nlocalhost:postgresql->otherhost:3331"]).get_endpoints()[1]
    assert remote_endpoint == "otherhost:3331"

    assert lsof_to_file([b"f6", b"au", b"tIPv6", b"d0x42",
                         b"nlocalhost:19091"]).get_endpoints()[1] is None
    assert lsof_to_file([b"f6", b"au", b"tIPv6", b"d0x42",
                         b"n*:57919"]).get_endpoints()[1] is None
    assert lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                         b"n*:57919"]).get_endpoints()[1] is None

    assert lsof_to_file([b"f6", b"au", b"tIPv4", b"d0x42",
                         b"n*:*"]).get_endpoints()[1] is None
    assert lsof_to_file([b"f6", b"aw", b"tREG", b"d0x42",
                         b"n/somefile"]).get_endpoints()[1] is None


def test_str_resolve():
    # FIXME: This will break if Google changes the name of 8.8.8.8
    test_me = px_file.PxFile()
    test_me.type = "IPv4"
    test_me.name = "127.0.0.1:51786->8.8.8.8:https"
    assert str(test_me) == "[IPv4] localhost:51786->google-public-dns-a.google.com:https"

    test_me = px_file.PxFile()
    test_me.type = "IPv4"
    test_me.name = "127.0.0.1:17600"
    assert str(test_me) == "[IPv4] localhost:17600 (LISTEN)"

    test_me = px_file.PxFile()
    test_me.type = "IPv6"
    test_me.name = "[::1]:17600"

    resolution = re.match("^\[IPv6\] (.*):17600 \(LISTEN\)$", str(test_me)).group(1)
    assert resolution == "[::1]" or "localhost" in resolution

    test_me = px_file.PxFile()
    test_me.type = "IPv4"
    test_me.name = "this:is:garbage:17600"
    assert str(test_me) == "[IPv4] this:is:garbage:17600 (LISTEN)"
