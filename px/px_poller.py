import os
import time
import threading

from . import px_load
from . import px_ioload
from . import px_meminfo
from . import px_process
from . import px_launchcounter

import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import Optional  # NOQA
    from typing import List  # NOQA
    from six import text_type


# We'll report poll done as this key having been pressed.
#
# NOTE: This must be detected as non-printable by handle_search_keypress().
POLL_COMPLETE_KEY = u"\x01"

# Key repeat speed is about one every 30+ms, and this pause needs to be longer
# than that for the pause to be useful while scrolling.
SHORT_PAUSE_SECONDS = 0.1


class PxPoller(object):
    def __init__(self, poll_complete_notification_fd=None):
        # type: (Optional[int]) -> None
        """
        After a poll is done and there is new data, a POLL_COMPLETE_KEY will be
        written to the poll_complete_notification_fd file descriptor.
        """
        self.thread = None  # type: Optional[threading.Thread]

        self.poll_complete_notification_fd = poll_complete_notification_fd

        self.lock = threading.Lock()

        self._ioload = px_ioload.PxIoLoad()
        self._ioload_string = u"None"

        self._loadstring = u"None"

        self._meminfo = u"None"

        self._all_processes = []  # type: List[px_process.PxProcess]

        self._launchcounter = px_launchcounter.Launchcounter()
        self._launchcounter_screen_lines = []  # type: List[text_type]

        # No process polling until this timestamp, timestamp from time.time()
        self._pause_process_updates_until = 0.0

        # Ensure we have current data already at the start
        self.poll_once()

    def pause_process_updates_a_bit(self):
        with self.lock:
            self._pause_process_updates_until = time.time() + SHORT_PAUSE_SECONDS

    def start(self):
        assert not self.thread

        self.thread = threading.Thread(name="Poller", target=self.poller)
        self.thread.daemon = True
        self.thread.start()

    def poll_once(self):
        with self.lock:
            if time.time() < self._pause_process_updates_until:
                return

        # Poll processes
        all_processes = px_process.get_all()
        with self.lock:
            self._all_processes = all_processes

        # Keep a launchcounter rendering up to date
        self._launchcounter.update(all_processes)
        launchcounter_screen_lines = self._launchcounter.get_screen_lines()
        with self.lock:
            self._launchcounter_screen_lines = launchcounter_screen_lines

        # Poll memory
        meminfo = px_meminfo.get_meminfo()
        with self.lock:
            self._meminfo = meminfo

        # Poll system load
        load = px_load.get_load_values()
        loadstring = px_load.get_load_string(load)
        with self.lock:
            self._loadstring = loadstring

        # Poll IO
        self._ioload.update()
        ioload_string = self._ioload.get_load_string()
        with self.lock:
            self._ioload_string = ioload_string

        # Notify fd that we have new data
        if self.poll_complete_notification_fd is not None:
            os.write(
                self.poll_complete_notification_fd, POLL_COMPLETE_KEY.encode("utf-8")
            )

    def poller(self):
        while True:
            with self.lock:
                sleeptime = self._pause_process_updates_until - time.time()
            if sleeptime < 0.0:
                sleeptime = 1.0
            time.sleep(sleeptime)
            self.poll_once()

    def get_all_processes(self):
        # type: () -> List[px_process.PxProcess]
        with self.lock:
            return self._all_processes

    def get_ioload_string(self):
        # type: () -> text_type
        with self.lock:
            return self._ioload_string

    def get_launchcounter_lines(self):
        # type: () -> List[text_type]
        with self.lock:
            return self._launchcounter_screen_lines

    def get_meminfo(self):
        # type: () -> text_type
        with self.lock:
            return self._meminfo

    def get_loadstring(self):
        # type: () -> text_type
        with self.lock:
            return self._loadstring
