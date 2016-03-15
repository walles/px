import sys
import copy
import time
import operator

import px_process
import px_terminal


def adjust_cpu_times(current, baseline):
    """
    Identify processes in current that are also in baseline.

    For all matches, substract the baseline process' CPU time usage from the
    current process' one.

    This way we get CPU times computed from when "px --top" was started, rather
    than from when each process was started.

    Neither current nor baseline are changed by this function.
    """
    pid2proc = {}
    for proc in current:
        pid2proc[proc.pid] = proc

    for baseline_proc in baseline:
        current_proc = pid2proc.get(baseline_proc.pid)
        if current_proc is None:
            # This process is newer than the baseline
            continue

        if current_proc.start_time != baseline_proc.start_time:
            # This PID has been reused
            continue

        if current_proc.cpu_time_seconds is None:
            # We can't substract from None
            continue

        if baseline_proc.cpu_time_seconds is None:
            # We can't substract None
            continue

        current_proc = copy.copy(current_proc)
        current_proc.set_cpu_time_seconds(
            current_proc.cpu_time_seconds - baseline_proc.cpu_time_seconds)
        pid2proc[current_proc.pid] = current_proc

    return pid2proc.values()


def top():
    baseline = px_process.get_all()
    while True:
        adjusted = adjust_cpu_times(px_process.get_all(), baseline)

        window_size = px_terminal.get_window_size()
        if window_size is None:
            sys.stderr.write("Cannot find terminal window size, are you on a terminal?\n")
            exit(1)

        # Sort by CPU time used, then most interesting first
        ordered = px_process.order_best_first(adjusted)
        ordered = sorted(ordered, key=operator.attrgetter('cpu_time_seconds'), reverse=True)
        rows, columns = window_size
        lines = px_terminal.to_screen_lines(ordered, columns)

        # Clear the screen and move cursor to top left corner:
        # https://en.wikipedia.org/wiki/ANSI_escape_code
        #
        # Note that some experimentation was involved in coming up with this
        # exact sequence; if you do first "clear" then "home" for example, the
        # contents of the previous screen gets added to the scrollback buffer,
        # which isn't what we want. Tread carefully if you intend to change
        # these.
        CSI = "\x1b["
        sys.stderr.write(CSI + "1J")
        sys.stderr.write(CSI + "H")

        sys.stdout.write("\n".join(lines[0:rows]))
        sys.stdout.flush()

        # FIXME: Interrupt sleep and iterate if terminal window is resized
        # FIXME: Interrupt sleep and terminate if user presses "q"
        time.sleep(1)

    return
