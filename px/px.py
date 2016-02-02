#!/usr/bin/python

import psutil

print "CPU loads: " + str(psutil.cpu_times())
