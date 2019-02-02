#!/usr/bin/env python
"""
Run tests using pytest but only ones that need rerunning
"""

import os

import pytest
import coverage
import datetime
import dateutil.tz

# FIXME: Figure these out dynamically
TEST_FILE = "tests/px_file_test.py"
TEST_NAME = "test_listen_name"  # NOTE: The slow one is "test_get_all"

# Run test and collect coverage data
cov = coverage.Coverage()
cov.start()
pytest.main(args=[TEST_FILE + "::" + TEST_NAME])
cov.stop()
coverage_data = cov.get_data()

# FIXME: If the test failed, drop it from the cache

# Print covered files
for file in coverage_data.measured_files():
    epoch_timestamp = os.path.getmtime(file)
    datetime_timestamp = datetime.datetime.fromtimestamp(epoch_timestamp, dateutil.tz.tzlocal())

    print(datetime_timestamp.isoformat(), " ", file)
