import os
import subprocess

import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type  # NOQA
    from typing import List  # NOQA
    from typing import Dict  # NOQA


ENV = {}  # type: Dict[str, str]
for name, value in os.environ.items():
    if name == "LANG":
        continue
    if name.startswith("LC_"):
        continue
    ENV[name] = value


def run(command, check_exitcode=False):
    # type: (List[str], bool) -> text_type
    run = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV
    )
    stdout = run.communicate()[0].decode("utf-8")

    if check_exitcode and run.returncode != 0:
        raise subprocess.CalledProcessError(run.returncode, command)

    return stdout
