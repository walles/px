#!/usr/bin/env python3

import os
import re
import subprocess

from setuptools import setup

from devbin import update_version_py

update_version_py.main()

git_version = (
    subprocess.check_output(["git", "describe", "--dirty"]).decode("utf-8").strip()
)

requirements = None
with open("requirements.txt", encoding="utf-8") as reqsfile:
    requirements = reqsfile.readlines()

with open(
    os.path.join(os.path.dirname(__file__), "README.rst"), encoding="utf-8"
) as fp:
    LONG_DESCRIPTION = fp.read()

if not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", git_version):
    # Setuptools wants nice version numbers
    git_version = "0.0.0"

setup(
    name="pxpx",
    version=git_version,
    description="ps and top for Human Beings",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/x-rst",
    author="Johan Walles",
    author_email="johan.walles@gmail.com",
    url="https://github.com/walles/px",
    license="MIT",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    packages=["px"],
    install_requires=requirements,
    # See: http://setuptools.readthedocs.io/en/latest/setuptools.html#setting-the-zip-safe-flag
    zip_safe=True,
    setup_requires=[
        "pytest-runner",
    ],
    tests_require=[
        "pytest",
    ],
    entry_points={
        "console_scripts": [
            "px = px.px:main",
            "ptop = px.px:main",
            "pxtree = px.px:main",
        ],
    },
    # Note that we're by design *not* installing man pages here.
    # Using "data_files=" only puts the man pages in the egg file,
    # and installing that egg doesn't put them on the destination
    # system.
    #
    # After trying to figure this out for a bit, my conclusion is
    # that "pip install" simply isn't meant for installing any man
    # pages.
    #
    #   /johan.walles@gmail.com 2018aug27
)
