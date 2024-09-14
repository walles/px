#!/usr/bin/env python3

import os
import re

from setuptools import setup

from px import version

try:
    from devbin import update_version_py

    update_version_py.main()
except ModuleNotFoundError:
    print("Devbin not found, assuming source distribution, not updating version.py")

with open(
    os.path.join(os.path.dirname(__file__), "README.rst"), encoding="utf-8"
) as fp:
    LONG_DESCRIPTION = fp.read()

version_for_setuptools = version.VERSION
if not re.match(r"^[0-9]+\.[0-9]+\.[0-9]+$", version_for_setuptools):
    # Setuptools wants nice version numbers
    version_for_setuptools = "0.0.0"

setup(
    name="pxpx",
    version=version_for_setuptools,
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
    # See: http://setuptools.readthedocs.io/en/latest/setuptools.html#setting-the-zip-safe-flag
    zip_safe=True,
    setup_requires=[
        "pytest-runner",
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
