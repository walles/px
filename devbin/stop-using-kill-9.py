#!/usr/bin/env python

import os
import time
import signal

def receiveSignal(signalNumber, frame):
    print('Received:', signalNumber)
    return

signal.signal(signal.SIGTERM, receiveSignal)

print('Waiting to be killed using "kill -9 ' + str(os.getpid()) + '"...')
while True:
    time.sleep(1234)
