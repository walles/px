#!/usr/bin/python

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
            'username',
            'memory_percent',
            'cpu_times',
            'cmdline'])
    except psutil.NoSuchProcess:
        pass
    else:
        print(pinfo)
