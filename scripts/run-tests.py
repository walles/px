#!/usr/bin/env python
"""
Run tests using pytest but only ones that need rerunning
"""

import os
import re
import sys
import glob
import time
import errno
import hashlib

import pytest
import coverage

CACHEROOT = '.pytest-avoidance'


def get_vm_identifier():
    """
    Returns a Python VM identifier "python-1.2.3-HASH", where the
    HASH is a hash of the VM contents and its location on disk.
    """

    (major, minor, micro, releaselevel, serial) = sys.version_info

    # From: https://stackoverflow.com/a/3431838/473672
    hash_md5 = hashlib.md5()
    with open(sys.executable, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    hash_md5.update(sys.executable.encode('utf-8'))
    hash = hash_md5.hexdigest()

    return "python-{}.{}.{}-{}".format(major, minor, micro, hash)


VM_IDENTIFIER = get_vm_identifier()


# From: https://stackoverflow.com/a/600612/473672
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_depsfile_name(test_file, test_name):
    # Dependencies file naming scheme:
    # .pytest-avoidance/<VM-identifier>/<path to .py file>/testname.deps

    test_file = os.path.abspath(test_file)
    if test_file[1] == ':':
        # Somebody on a Windows box, please test this
        test_file = test_file.replace(':', '/', 1)
    if test_file[0] == '/':
        # Starting the path with '/' would mess up os.path.join()
        test_file = test_file[1:]

    cachedir = os.path.join(CACHEROOT, VM_IDENTIFIER, test_file)

    mkdir_p(cachedir)
    depsfile_name = os.path.join(cachedir, test_name + ".deps")

    return depsfile_name


def run_test(test_file, test_name):
    """
    Run test and collect coverage data.

    Returns 0 on success and other numbers on failure.
    """
    cov = coverage.Coverage()
    cov.start()
    try:
        exitcode = pytest.main(args=[test_file + "::" + test_name])
        if exitcode is not 0:
            # We don't cache failures
            return exitcode
    finally:
        cov.stop()
    coverage_data = cov.get_data()

    with open(get_depsfile_name(test_file, test_name), "w") as depsfile:
        for filename in coverage_data.measured_files():
            depsfile.write("%s\n" % (filename,))

    return 0


def has_cached_success(test_file, test_name):
    depsfile_name = get_depsfile_name(test_file, test_name)
    if not os.path.isfile(depsfile_name):
        # Nothing cached for this test
        print("Cache entry doesn't exist, no hit: " + depsfile_name)
        return False

    cache_timestamp = os.path.getmtime(depsfile_name)
    with open(depsfile_name, 'r') as depsfile:
        for depsline in depsfile:
            filename = depsline.rstrip()
            if not os.path.isfile(filename):
                # Dependency is gone
                print("Dependency gone, no hit: " + filename)
                return False

            file_timestamp = os.path.getmtime(filename)

            if file_timestamp > cache_timestamp:
                # Dependency updated
                print("Dependency updated, no hit: " + filename)
                return False

    # No mismatch found for this test, it's a cache hit!
    return True


def maybe_run_test(test_file, test_name):
    """
    Produce test result, from cache or from real run.

    Returns 0 on success and other numbers on failure.
    """
    if has_cached_success(test_file, test_name):
        print("[CACHED]: SUCCESS: %s::%s" % (test_file, test_name))
        return 0
    else:
        return run_test(test_file, test_name)


# Discover these like pytest does
passcount = 0
failcount = 0
t0 = time.time()
TEST_FUNCTION = re.compile("^def (test_[^)]+)\\(")
for testfile_name in glob.glob("tests/*_test.py"):
    with open(testfile_name, 'r') as testfile:
        for line in testfile:
            matches = TEST_FUNCTION.match(line.rstrip())
            if not matches:
                continue
            test_name = matches.group(1)
            exitcode = maybe_run_test(testfile_name, test_name)
            if exitcode is 0:
                passcount += 1
            else:
                failcount += 1
t1 = time.time()
dt = t1 - t0

print("")
print("{} tests run in {}s".format(passcount + failcount, int(dt)))
print("PASS: {}".format(passcount))
print("FAIL: {}".format(failcount))

print("")
if failcount > 0:
    print("There were failures!")
    sys.exit(1)
else:
    print("All tests passed!")
    sys.exit(0)
