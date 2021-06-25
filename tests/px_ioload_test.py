# -*- coding: utf-8 -*-

import os
from px import px_ioload


def test_parse_netstat_ib_output():
    my_dir = os.path.dirname(__file__)
    sample_netstat_ib_output_path = os.path.join(my_dir, "netstat-ib.txt")
    with open(sample_netstat_ib_output_path) as sample_netstat_ib_output_file:
        sample_netstat_ib_output = sample_netstat_ib_output_file.read()

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
