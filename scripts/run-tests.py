#!/usr/bin/env python
"""
Run tests using pytest but only ones that need rerunning
"""

import os

import errno
import pytest
import coverage

CACHEROOT = '.pytest-avoidance'

# FIXME: This should be python-<version>-<hash-of-the-python-binary>
VM_IDENTIFIER = 'python-1.2.3'


# From: https://stackoverflow.com/a/600612/473672
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def get_depsfile_name(test_file, test_name):
    # Dependencies file naming scheme:
    # .pytest-avoidance/<VM-identifier>/<path to .py file>/testname.deps

    # FIXME: Ensure test_file path doesn't start with "/", or CACHEROOT and VM_IDENTIFIER
    # will be dropped by os.path.join()
    cachedir = os.path.join(CACHEROOT, VM_IDENTIFIER, test_file)

    print ("Cachedir name: " + cachedir)
    mkdir_p(cachedir)
    depsfile_name = os.path.join(cachedir, test_name + ".deps")
    print ("Depsfile name: " + depsfile_name)

    return depsfile_name


def run_test(test_file, test_name):
    # Run test and collect coverage data
    cov = coverage.Coverage()
    cov.start()
    exitcode = pytest.main(args=[test_file + "::" + test_name])
    if exitcode is not 0:
        # FIXME: Remove any cached data for this test and run the next one instead
        pass

    cov.stop()
    coverage_data = cov.get_data()

    with open(get_depsfile_name(test_file, test_name), "w") as depsfile:
        for filename in coverage_data.measured_files():
            depsfile.write("%s\n" % (filename,))


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
                # FIXME: Remove this cache entry here?
                print("Dependency gone, no hit: " + filename)
                return False

            file_timestamp = os.path.getmtime(filename)

            if file_timestamp > cache_timestamp:
                # Dependency has changed
                # FIXME: Remove this cache entry here?
                print("Dependency timestamp mismatch, no hit: " + filename)
                return False

    # No mismatch found for this test, it's a cache hit!
    return True


def maybe_run_test(test_file, test_name):
    if has_cached_success(test_file, test_name):
        print("[CACHED]: SUCCESS: %s::%s" % (test_file, test_name))
    else:
        run_test("tests/px_file_test.py", "test_listen_name")


# FIXME: Discover these like pytest does
maybe_run_test("tests/px_file_test.py", "test_listen_name")
