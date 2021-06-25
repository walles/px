"""
Functions for visualizing where IO is bottlenecking.
"""

class PxIoLoad(object):
    def update(self):
        # type: () -> None
        #
        # Measure stuff on the current system
        pass

    def get_load_string(self):
        """
        Example return value: "14%  [123B/s / 878B/s] eth0 outgoing"
        """
        return "14%  [123B/s / 878B/s] eth0 outgoing"

_ioload = PxIoLoad()


def update():
    _ioload.update()


def get_load_string():
    return _ioload.get_load_string()
