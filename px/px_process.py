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


def get_all():
    process_builder = PxProcessBuilder()
    process_builder.pid = 7
    process_builder.username = "adsggeqeqtetq"
    process_builder.cpu_time = 1.3
    process_builder.memory_percent = 42.7
    process_builder.cmdline = "hej kontinent"

    return [PxProcess(process_builder)]
