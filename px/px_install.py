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
        raise OSError(f"Source is not a file: {src}")

    parent = os.path.dirname(dest)
    if not os.path.isdir(parent):
        raise OSError(f"Destination parent is not a directory: {parent}")

    if os.path.isdir(dest):
        raise OSError(f"Destination is a directory, won't replace that: {dest}")

    # Make sure nothing's in the way
    try:
        os.remove(dest)
    except OSError:
        pass
    if os.path.exists(dest):
        raise OSError(f"Can't remove existing entry: {dest}")

    shutil.copyfile(src, dest)
    os.chmod(dest, 0o755)
