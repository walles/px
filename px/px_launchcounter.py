import sys

from . import px_process

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List    # NOQA


class Launchcounter(object):
    def update(self, procs_snapshot):
        # type: (List[px_process.PxProcess]) -> None
        pass

    def get_launched_screen_lines(self, rows, columns):
        return ["FIXME"] * rows

    def get_launchers_screen_lines(self, rows, columns):
        return ["FIXME"] * rows
