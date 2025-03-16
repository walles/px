#!/usr/bin/env python3

"""
Build the project from a clean clone to make sure that works.
"""

import os
import sys
import shutil
import subprocess
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
print("Building sources using setup.py...")
subprocess.run(["python3", "setup.py", "build"], cwd=tempdir, check=True)

print("Building sources using python -m build...")
FAKE_VERSION = "99.99.99"
subprocess.run(
    [
        "git",
        "commit",
        "--all",
        "--allow-empty",
        "--message",
        "Ensure we're clean before building the wheel",
    ]
)
subprocess.run(["git", "tag", "--force", FAKE_VERSION], cwd=tempdir, check=True)

# This is what tox.ini does in test-wheel
subprocess.run(
    [
        "python3",
        "-m",
        "build",
        "--outdir",
        "dist",
    ],
    cwd=tempdir,
    check=True,
)

# Check that no files in dist have "0.0.0" in their names
print(f"Checking that all files in dist have '{FAKE_VERSION}' in their names...")
found_misversioned = False
for filename in os.listdir(os.path.join(tempdir, "dist")):
    if FAKE_VERSION not in filename:
        print(f"{FAKE_VERSION} not in <{filename}>")
        found_misversioned = True
if found_misversioned:
    print(f"{FAKE_VERSION} not found all dist/ filenames, failing...")
    sys.exit(1)

shutil.rmtree(tempdir)
