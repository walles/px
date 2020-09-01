import os
import subprocess

import sys
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type  # NOQA
    from typing import List  # NOQA
    from typing import Dict  # NOQA


def run(command):
    # type: (List[str]) -> text_type
    env = {}  # type: Dict[str, str]
    for name, value in os.environ.items():
        if name == "LANG":
            continue
        if name.startswith("LC_"):
            continue
        env[name] = value

    run = subprocess.Popen(command,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           env=env)
    stdout = run.communicate()[0].decode('utf-8')

    return stdout
