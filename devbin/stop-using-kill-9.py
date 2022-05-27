#!/usr/bin/env python3

import os
import time
import signal


def receiveSignal(signalNumber, _):
    print("Received signal " + str(signalNumber))


signal.signal(signal.SIGTERM, receiveSignal)

print('Waiting to be killed using "kill -9 ' + str(os.getpid()) + '"...')
while True:
    time.sleep(1234)
