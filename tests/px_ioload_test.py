# -*- coding: utf-8 -*-

import os
from px import px_ioload

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type


def load(sample_file_name):
    # type: (text_type) -> text_type
    my_dir = os.path.dirname(__file__)
    full_path = os.path.join(my_dir, sample_file_name)
    with open(full_path) as sample_file:
        return sample_file.read()


def test_parse_netstat_ib_output():
    sample_netstat_ib_output = load("netstat-ib.txt")

    expected = [
        px_ioload.Sample("lo0 incoming", 903920),
        px_ioload.Sample("lo0 outgoing", 903920),
        px_ioload.Sample("en0 incoming", 1410907682),
        px_ioload.Sample("en0 outgoing", 67569820),
        px_ioload.Sample("awdl0 incoming", 0),
        px_ioload.Sample("awdl0 outgoing", 11760),
        px_ioload.Sample("utun0 incoming", 0),
        px_ioload.Sample("utun0 outgoing", 200),
        px_ioload.Sample("utun1 incoming", 0),
        px_ioload.Sample("utun1 outgoing", 200),
    ]
    actual = px_ioload.parse_netstat_ib_output(sample_netstat_ib_output)

    assert actual == expected


def test_parse_iostat_output():
    sample_iostat_output = load("iostat-dki-n-99.txt")

    expected = [ px_ioload.Sample("disk0", 46066166661) ]
    actual = px_ioload.parse_iostat_output(sample_iostat_output)

    assert actual == expected
