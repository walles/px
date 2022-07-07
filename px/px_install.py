import sys
import shutil

import os


def install(src, dest):
    """
    Copy src (file) into dest (file) and make dest executable.

    On trouble, prints message and exits with an error code.
    """
    try:
        _install(src, dest)
    except Exception as e:  # pylint: disable=broad-except
        sys.stderr.write(f"Installing {dest} failed, please retry with sudo\n")
        sys.stderr.write(f"Error was: {str(e)}\n")
        sys.exit(1)
    print(f"Created: {dest}")


def _install(src, dest):
    """
    Copy src (file) into dest (file) and make dest executable.

    Throws exception on trouble.
    """
    if os.path.realpath(src) == os.path.realpath(dest):
        # Copying a file onto itself is a no-op, never mind
        return

    if not os.path.isfile(src):
        raise OSError("Source is not a file: {}".format(src))

    parent = os.path.dirname(dest)
    if not os.path.isdir(parent):
        raise OSError("Destination parent is not a directory: {}".format(parent))

    if os.path.isdir(dest):
        raise OSError("Destination is a directory, won't replace that: {}".format(dest))

    # Make sure nothing's in the way
    try:
        os.remove(dest)
    except OSError:
        pass
    if os.path.exists(dest):
        raise OSError("Can't remove existing entry: {}".format(dest))

    shutil.copyfile(src, dest)
    os.chmod(dest, 0o755)
