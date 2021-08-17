import os
import time
import threading

from . import px_process
from . import px_ioload

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List        # NOQA
    import six


# We'll report poll done as this key having been pressed.
#
# NOTE: This must be detected as non-printable by handle_search_keypress().
POLL_COMPLETE_KEY = u'\x01'

class PxPoller(object):
    def __init__(self, poll_complete_notification_fd):
        """
        After a poll is done and there is new data, a POLL_COMPLETE_KEY will be
        written to the poll_complete_notification_fd file descriptor.
        """
        self.poll_complete_notification_fd = poll_complete_notification_fd

        self.lock = threading.Lock()
        self._ioload = px_ioload.PxIoLoad()
        self._ioload_string = None  # type: six.text_type
        self._all_processes = None  # type: List[px_process.PxProcess]  # type: ignore

        # Ensure we have current data already at the start
        self.poll_once()

        self.thread = threading.Thread(name="Poller", target=self.poller)
        self.thread.daemon = True
        self.thread.start()

    def poll_once(self):
        # Poll processes
        all_processes = px_process.get_all()
        with self.lock:
            self._all_processes = all_processes

        # FIXME: Poll memory

        # Poll IO
        self._ioload.update()
        ioload_string = self._ioload.get_load_string()
        with self.lock:
            self._ioload_string = ioload_string

        # Notify fd that we have new data
        os.write(
            self.poll_complete_notification_fd,
            POLL_COMPLETE_KEY.encode("utf-8"))


    def poller(self):
        while True:
            time.sleep(1.0)
            self.poll_once()

    def get_all_processes(self):
        # type: () -> List[px_process.PxProcess]
        with self.lock:
            return self._all_processes

    def get_ioload_string(self):
        with self.lock:
            return self._ioload_string
