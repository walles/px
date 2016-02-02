#!/usr/bin/python

import os
import psutil

# List all processes, and print for each process: PID, owner,
# memory usage (in %), used CPU time and full command line
#
# FIXME: Print in columns
#
# FIXME: Sort printed list by (memory usage) * (used CPU time)
for proc in psutil.process_iter():
    try:
        pinfo = proc.as_dict(attrs=[
            'pid',
            'exe',
            'username',
            'memory_percent',
            'cpu_times',
            'cmdline'])
    except psutil.NoSuchProcess:
        pass
    else:
        pid = pinfo['pid']
        user = pinfo['username']

        cpu_time = None
        cpu_times = pinfo['cpu_times']
        if cpu_times is not None:
            if cpu_times.user is not None and cpu_times.system is not None:
                cpu_time = cpu_times.user + cpu_times.system
        if cpu_time is None:
            cpu_time_s = "--"
        else:
            cpu_time_s = "{:.3f}s".format(cpu_time)

        memory_percent = pinfo['memory_percent']
        if memory_percent is None:
            memory_percent_s = "--"
        else:
            memory_percent_s = "{:.0f}%".format(memory_percent)

        cmdline = pinfo['cmdline']
        if cmdline is None:
            exe = pinfo['exe']
            cmdline = exe + " [...]"

        print("{:>6} {:9} {:>9} {:>4} {}".format(
            pid, user, cpu_time_s, memory_percent_s, cmdline))
