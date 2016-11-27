from px import px_terminal

import testutils


def test_to_screen_lines_unbounded():
    procs = [testutils.create_process(commandline="/usr/bin/fluff 1234")]
    assert px_terminal.to_screen_lines(procs, None) == [
        "  PID COMMAND USERNAME   CPU RAM COMMANDLINE",
        "47536 fluff   root     0.03s  0% /usr/bin/fluff 1234"
    ]
