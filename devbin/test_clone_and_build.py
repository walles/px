#!/usr/bin/env python3

"""
Build the project from a clean clone to make sure that works.
"""

import shutil
import subprocess
import tempfile

# Copy everything to a temporary directory
tempdir = tempfile.mkdtemp()
print(f"Copying sources into {tempdir}...")
shutil.copytree(
    ".",
    tempdir,
    dirs_exist_ok=True,
    ignore=shutil.ignore_patterns(
        ".tox", "env", ".mypy_cache", ".pytest_cache", "__pycache__"
    ),
)

# Remove any artifacts so the build is clean
print("Cleaning sources...")
subprocess.run(
    [
        "git",
        "clean",
        "-d",
        "--force",
        "-x",
        "--quiet",
    ],
    cwd=tempdir,
)

# Build the clone
print("Building sources...")
subprocess.run(["python3", "setup.py", "build"], cwd=tempdir, check=True)

shutil.rmtree(tempdir)
