#!/bin/bash

set -o pipefail
set -e
set -x

if [ "$VIRTUAL_ENV" ] ; then
  echo 'ERROR: Already in a virtualenv, do "deactivate" first and try again'
  exit 1
fi

PX_PEX='bazel-bin/px'

# FIXME: Once this works, just remove it since it will be done further down
# anyway, after linting and testing.
bazel build --build_python_zip px && "${PX_PEX}"

# The "suffix" needs to be different for caching to work properly
# FIXME: Use scripts/set-other-python.sh to identify two different Pythons
bazel test --test_output=errors --python_path=/usr/local/bin/python2 --platform_suffix=py2 unittests
bazel test --test_output=errors --python_path=/usr/local/bin/python3 --platform_suffix=py3 unittests
# FIXME: Make bazel run shellcheck ./*.sh ./*/*.sh
# FIXME: Make bazel run installtest.sh
# FIXME: Make bazel run flake8
# FIXME: On Python 3, make bazel run mypy in both Python2 and Python3 mode
# FIXME: Make bazel run: "px", "px $$", "px --version", "px bazel"
# FIXME: Collect coverage data from unit test runs

# FIXME: Make bazel run setup.py to create a py2.py3 wheel
# FIXME: Make bazel test px from the wheel using: "px", "px $$", "px --version", "px bazel"

bazel build --build_python_zip px

if unzip -qq -l "${PX_PEX}" '*.so' ; then
  cat << EOF
  ERROR: px contains natively compiled dependencies, this makes
         distribution a lot harder. Please fix the dependencies.
EOF
  exit 1
fi

if ! head -n1 "${PX_PEX}" | grep -w python ; then
  echo
  echo "ERROR: px should use \"python\" as its interpreter:"
  file "${PX_PEX}"
  exit 1
fi
