import os
import subprocess

from typing import List
from typing import Dict


ENV: Dict[str, str] = {}
for name, value in os.environ.items():
    if name == "LANG":
        continue
    if name.startswith("LC_"):
        continue
    ENV[name] = value


def run(command: List[str], check_exitcode: bool = False) -> str:
    with subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV
    ) as execution:
        stdout = execution.communicate()[0].decode("utf-8")

        if check_exitcode and execution.returncode != 0:
            raise subprocess.CalledProcessError(execution.returncode, command)

        return stdout
