#!/usr/bin/env python
"""
Run tests using pytest but only ones that need rerunning
"""

import pytest

# FIXME: Figure these out dynamically
TEST_FILE = "tests/px_file_test.py"
TEST_NAME = "test_listen_name"  # NOTE: The slow one is "test_get_all"

pytest.main(args=[TEST_FILE + "::" + TEST_NAME])
