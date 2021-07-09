# -*- coding: utf-8 -*-

from . import testutils

from px import px_ioload

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type


def test_parse_netstat_ib_output():
    sample_netstat_ib_output = testutils.load("netstat-ib.txt")

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
    sample_iostat_output = testutils.load("iostat-dki-n-99.txt")

    expected = [ px_ioload.Sample("disk0", 46066166661) ]
    actual = px_ioload.parse_iostat_output(sample_iostat_output)

    assert actual == expected


def test_parse_proc_net_dev():
    proc_net_dev_contents = testutils.load("proc-net-dev.txt")

    # No data expected for the all-zero interfaces lo, tunl0 and ip6tnl0
    expected = [
        px_ioload.Sample("eth0 incoming", 29819439),
        px_ioload.Sample("eth0 outgoing", 364327),
    ]
    actual = px_ioload.parse_proc_net_dev(proc_net_dev_contents)

    assert actual == expected
