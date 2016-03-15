import sys
import time

import px_process
import px_terminal


def adjust_cpu_times(current, baseline):
    # FIXME: Identify the same processes in current and baseline, and substract
    # the baseline CPU time from all current matches
    return current


def to_screen_lines(processes, columns):
    # FIXME: Turn a process list into a list of rows that can be printed to
    # screen. Each row should be truncated to be at most columns long.
    #
    # Should most likely call the same code as in px.py
    return ["imagine", "a", "process", "list", "here"]


def top():
    baseline = px_process.get_all()

    current = baseline
    while True:
        adjusted = adjust_cpu_times(current, baseline)

        window_size = px_terminal.get_window_size()
        if window_size is None:
            # FIXME: Print helpful error message
            exit(1)

        rows, columns = window_size
        lines = px_terminal.to_screen_lines(px_process.order_best_first(adjusted), columns)

        # FIXME: Clear the screen
        print("FIXME: Clear the screen")

        sys.stdout.write("\n".join(lines[0:rows]))
        sys.stdout.flush()

        # FIXME: Interrupt sleep and iterate if terminal window is resized
        time.sleep(1)

    return
