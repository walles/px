#!/usr/bin/env python3

"""
Build the project from a clean clone to make sure that works.
"""

import os
import shutil
import subprocess
import sys
import tempfile

# Copy everything to a temporary directory
tempdir = tempfile.mkdtemp()
print(f"Copying sources into <{tempdir}>...")
shutil.copytree(
    ".",
    tempdir,
    dirs_exist_ok=True,
    ignore=shutil.ignore_patterns(
        ".tox", "env", ".mypy_cache", ".pytest_cache", "__pycache__"
    ),
)
os.chdir(tempdir)

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
    check=True,
)

# Build the clone
print("Building sources using python -m build...")
FAKE_VERSION = "99.99.99"
subprocess.run(["git", "config", "user.email", "you@example.com"], check=True)
subprocess.run(["git", "config", "user.name", "Your Name"], check=True)
subprocess.run(
    [
        "git",
        "commit",
        "--all",
        "--allow-empty",
        "--message",
        "Ensure we're clean before building the wheel",
    ],
    check=True,
)
subprocess.run(
    [
        "git",
        "tag",
        "--annotate",
        "--force",
        "--message",
        "Forced tag for testing the build",
        FAKE_VERSION,
    ],
    check=True,
)

# This is what tox.ini does in test-wheel
subprocess.run(
    [
        "python3",
        "-m",
        "build",
        "--outdir",
        "dist",
    ],
    check=True,
)

# Check that no files in dist have "0.0.0" in their names
print(f"Checking that all files in dist have '{FAKE_VERSION}' in their names...")
found_misversioned = False
for filename in os.listdir("dist"):
    if FAKE_VERSION not in filename:
        print(f"{FAKE_VERSION} not in <{filename}>")
        found_misversioned = True
if found_misversioned:
    print(f"{FAKE_VERSION} not found all dist/ filenames, failing...")
    sys.exit(1)

shutil.rmtree(tempdir)
