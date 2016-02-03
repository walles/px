import psutil


class PxProcess:
    def __init__(self, psutil_process):
        self.pid = psutil_process.pid
        self.user = psutil_process.username()

        try:
            cpu_times = psutil_process.cpu_times()
            cpu_time = cpu_times.user + cpu_times.system
            self.cpu_time_s = "{:.3f}s".format(cpu_time)
        except psutil.AccessDenied:
            self.cpu_time_s = "--"
        except psutil.ZombieProcess:
            # On OS X 10.11.2 and psutil 3.4.2 this sometimes happens for
            # ordinary processes when we aren't root, treat as AccessDenied.
            self.cpu_time_s = "--"

        try:
            memory_percent = psutil_process.memory_percent()
            self.memory_percent_s = "{:.0f}%".format(memory_percent)
        except psutil.AccessDenied:
            self.memory_percent_s = "--"
        except psutil.ZombieProcess:
            # On OS X 10.11.2 and psutil 3.4.2 this sometimes happens for
            # ordinary processes when we aren't root, treat as AccessDenied.
            self.memory_percent_s = "--"

        try:
            self.cmdline = psutil_process.cmdline()
        except psutil.AccessDenied:
            self.cmdline = psutil_process.exe() + " [...]"
        except psutil.ZombieProcess:
            # On OS X 10.11.2 and psutil 3.4.2 this sometimes happens for
            # ordinary processes when we aren't root, treat as AccessDenied.
            self.cmdline = psutil_process.exe() + " [...]"
