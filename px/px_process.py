import subprocess


class PxProcess(object):
    def __init__(self, process_builder):
        self.pid = process_builder.pid

        self.user = process_builder.username

        self.cpu_time_s = "{:.3f}s".format(process_builder.cpu_time)

        self.memory_percent_s = (
            "{:.0f}%".format(process_builder.memory_percent))

        self.cmdline = process_builder.cmdline

        self.score = (
            (process_builder.cpu_time + 1) *
            (process_builder.memory_percent + 1))


class PxProcessBuilder(object):
    pass


def call_ps():
    """
    Call ps and return the result in an array of one output line per process
    """
    ps = subprocess.Popen(["ps", "-ax", "-o", "pid,user,time,%mem,command"],
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return ps.communicate()[0].splitlines()[1:]


def ps_line_to_process(ps_line):
    process_builder = PxProcessBuilder()
    process_builder.pid = 7
    process_builder.username = "adsggeqeqtetq"
    process_builder.cpu_time = 1.3
    process_builder.memory_percent = 42.7
    process_builder.cmdline = "hej kontinent"

    return PxProcess(process_builder)


def get_all():
    return map(lambda line: ps_line_to_process(line), call_ps())
