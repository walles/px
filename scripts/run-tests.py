#!/usr/bin/env python
"""
Run tests using pytest but only ones that need rerunning
"""

import os

import errno
import pytest
import coverage
import datetime
import dateutil.tz

CACHEROOT = '.pytest-avoidance'

# FIXME: This should be python-<version>-<hash-of-the-python-binary>
VM_IDENTIFIER = 'python-1.2.3'

# FIXME: Figure these out dynamically
TEST_FILE = "tests/px_file_test.py"
TEST_NAME = "test_listen_name"  # NOTE: The slow one is "test_get_all"


# From: https://stackoverflow.com/a/600612/473672
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


# Run test and collect coverage data
cov = coverage.Coverage()
cov.start()
exitcode = pytest.main(args=[TEST_FILE + "::" + TEST_NAME])
if exitcode is not 0:
    # FIXME: Remove any cached data for this test and run the next one instead
    pass

cov.stop()
coverage_data = cov.get_data()

# Store the file-timestamps list into a file
#
# File naming scheme:
# .pytest-avoidance/<VM-identifier>/<path to .py file>/testname.deps

# FIXME: Ensure TEST_FILE path doesn't start with "/", or CACHEROOT and VM_IDENTIFIER
# will be dropped by os.path.join()
cachedir = os.path.join(CACHEROOT, VM_IDENTIFIER, TEST_FILE)

print ("Cachedir name: " + cachedir)
mkdir_p(cachedir)
depsfile_name = os.path.join(cachedir, TEST_NAME + ".deps")
print ("Depsfile name: " + depsfile_name)
# Now write our stuff into depsfile
with open(depsfile_name, "w") as depsfile:
    for file in coverage_data.measured_files():
        epoch_timestamp = os.path.getmtime(file)
        datetime_timestamp = datetime.datetime.fromtimestamp(epoch_timestamp, dateutil.tz.tzlocal())
        depsfile.write("%s %s\n" % (datetime_timestamp.isoformat(), file))
