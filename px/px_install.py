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
    except Exception as e:
        sys.stderr.write("Installing {} failed, please retry with sudo\n".format(dest))
        sys.stderr.write("Error was: {}\n".format(str(e)))
        exit(1)
    print("Created: {}".format(dest))


def _install(src, dest):
    """
    Copy src (file) into dest (file) and make dest executable.

    Throws exception on trouble.
    """
    if os.path.realpath(src) == os.path.realpath(dest):
        # Copying a file onto itself is a no-op, never mind
        return

    if not os.path.isfile(src):
        raise IOError("Source is not a file: %s" % (src,))

    parent = os.path.dirname(dest)
    if not os.path.isdir(parent):
        raise IOError("Destination parent is not a directory: %s" % (parent,))

    if os.path.isdir(dest):
        raise IOError("Destination is a directory, won't replace that: %s" % (dest,))

    # Make sure nothing's in the way
    try:
        os.remove(dest)
    except OSError:
        pass
    if os.path.exists(dest):
        raise IOError("Can't remove existing entry: %s" % (dest,))

    shutil.copyfile(src, dest)
    os.chmod(dest, 0o755)
