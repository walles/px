import os

from px import px_top
from px import px_poller
from px import px_process
from px import px_terminal
from px import px_launchcounter

from . import testutils


def test_adjust_cpu_times():
    now = testutils.now()

    current = [
        px_process.create_kernel_process(now),
        testutils.create_process(
            pid=100, cputime="0:10.00", commandline="only in current"
        ),
        testutils.create_process(
            pid=200,
            cputime="0:20.00",
            commandline="re-used PID baseline",
            timestring="Mon May  7 09:33:11 2010",
        ),
        testutils.create_process(
            pid=300, cputime="0:30.00", commandline="relevant baseline"
        ),
    ]
    baseline = [
        px_process.create_kernel_process(now),
        testutils.create_process(
            pid=200,
            cputime="0:02.00",
            commandline="re-used PID baseline",
            timestring="Mon Apr  7 09:33:11 2010",
        ),
        testutils.create_process(
            pid=300, cputime="0:03.00", commandline="relevant baseline"
        ),
        testutils.create_process(
            pid=400, cputime="0:03.00", commandline="only in baseline"
        ),
    ]

    actual = px_process.order_best_last(px_top.adjust_cpu_times(baseline, current))
    expected = px_process.order_best_last(
        [
            px_process.create_kernel_process(now),
            testutils.create_process(
                pid=100, cputime="0:10.00", commandline="only in current"
            ),
            testutils.create_process(
                pid=200,
                cputime="0:20.00",
                commandline="re-used PID baseline",
                timestring="Mon May  7 09:33:11 2010",
            ),
            testutils.create_process(
                pid=300, cputime="0:27.00", commandline="relevant baseline"
            ),
        ]
    )

    assert actual == expected


def test_get_toplist():
    # Just make sure this call doesn't crash
    px_top.get_toplist(px_process.get_all(), px_process.get_all())


def test_get_command():
    pipe = os.pipe()
    read, write = pipe
    os.write(write, b"q")

    assert px_top.get_command(timeout_seconds=0, fd=read) == px_top.CMD_QUIT


def test_sigwinch_handler():
    # Args ignored at the time of writing this, fill in better values if needed
    px_terminal.sigwinch_handler(None, None)

    # sys.stdin doesn't work when STDIN has been redirected (as during testing),
    # so we need to explicitly use the STDIN fd here. Try removing it and you'll
    # see :).
    STDIN = 0
    assert px_top.get_command(timeout_seconds=0, fd=STDIN) == px_top.CMD_RESIZE


def test_redraw():
    # Just make sure it doesn't crash
    baseline = px_process.get_all()
    poller = px_poller.PxPoller()
    px_top.redraw(baseline, poller, 100, 10)


def test_get_screen_lines_low_screen():
    baseline = px_process.get_all()
    poller = px_poller.PxPoller()

    SCREEN_ROWS = 10
    px_terminal._enable_color = True
    lines = px_top.get_screen_lines(baseline, poller, SCREEN_ROWS)

    # Top row should contain ANSI escape codes
    CSI = u"\x1b["
    assert u"CSI" in lines[0].replace(CSI, u"CSI")

    assert len(lines) == SCREEN_ROWS

    # Last line should be decorated
    assert u"CSI" in lines[-1].replace(CSI, u"CSI")


def test_get_screen_lines_high_screen():
    baseline = px_process.get_all()
    poller = px_poller.PxPoller()

    SCREEN_ROWS = 100
    px_terminal._enable_color = True
    lines = px_top.get_screen_lines(baseline, poller, SCREEN_ROWS)

    # Top row should contain ANSI escape codes
    CSI = u"\x1b["
    assert u"CSI" in lines[0].replace(CSI, u"CSI")

    assert len(lines) == SCREEN_ROWS

    # Last line should be decorated
    assert u"CSI" in lines[-1].replace(CSI, u"CSI")


def test_get_screen_lines_with_many_launches():
    baseline = px_process.get_all()
    launchcounter = px_launchcounter.Launchcounter()

    for i in range(1, 100):
        launchcounter._register_launches(
            [testutils.fake_callchain("init", "a" + str(i))]
        )

    poller = px_poller.PxPoller()
    poller._launchcounter = launchcounter
    poller._launchcounter_screen_lines = launchcounter.get_screen_lines()

    SCREEN_ROWS = 100
    lines = px_top.get_screen_lines(baseline, poller, SCREEN_ROWS)

    assert len(lines) == SCREEN_ROWS


def test_get_screen_lines_returns_enough_lines():
    baseline = px_process.get_all()
    poller = px_poller.PxPoller()

    SCREEN_ROWS = 100000
    lines = px_top.get_screen_lines(baseline, poller, SCREEN_ROWS)

    assert len(lines) == SCREEN_ROWS
