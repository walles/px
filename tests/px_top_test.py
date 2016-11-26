from px import px_top
from px import px_process

import testutils


def test_adjust_cpu_times():
    now = testutils.now()

    current = [
        px_process.create_kernel_process(now),
        testutils.create_process(pid=100, cputime="0:10.00", commandline="only in current"),
        testutils.create_process(pid=200, cputime="0:20.00", commandline="re-used PID baseline",
                                 timestring="Mon May 7 09:33:11 2010"),
        testutils.create_process(pid=300, cputime="0:30.00", commandline="relevant baseline"),
    ]
    baseline = [
        px_process.create_kernel_process(now),
        testutils.create_process(pid=200, cputime="0:02.00", commandline="re-used PID baseline",
                                 timestring="Mon Apr 7 09:33:11 2010"),
        testutils.create_process(pid=300, cputime="0:03.00", commandline="relevant baseline"),
        testutils.create_process(pid=400, cputime="0:03.00", commandline="only in baseline"),
    ]

    actual = px_process.order_best_last(px_top.adjust_cpu_times(current, baseline))
    expected = px_process.order_best_last([
        px_process.create_kernel_process(now),
        testutils.create_process(pid=100, cputime="0:10.00", commandline="only in current"),
        testutils.create_process(pid=200, cputime="0:20.00", commandline="re-used PID baseline",
                                 timestring="Mon May 7 09:33:11 2010"),
        testutils.create_process(pid=300, cputime="0:27.00", commandline="relevant baseline"),
    ])

    assert actual == expected
