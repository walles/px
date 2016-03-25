import re
import os.path


# Match "[kworker/0:0H]", no grouping
LINUX_KERNEL_PROC = re.compile("^\[[^/ ]+/?[^/ ]+\]$")

# Match "(python2.7)", no grouping
OSX_PARENTHESIZED_PROC = re.compile("^\([^()]+\)$")


def to_array(commandline):
    """Splits a command line string into components"""
    base_split = commandline.split(" ")
    if len(base_split) == 1:
        return base_split

    # Try to reverse engineer executables with spaces in their names
    merged_split = list(base_split)
    while not os.path.isfile(merged_split[0]):
        if len(merged_split) == 1:
            # Nothing more to merge, give up
            return base_split

        # Merge the two first elements: http://stackoverflow.com/a/1142879/473672
        merged_split[0:2] = [' '.join(merged_split[0:2])]

    return merged_split


def get_command(commandline):
    """
    Extracts the command from the command line.

    This function most often returns the first component of the command line
    with the path stripped away.

    For some language runtimes, this function may return the name of the program
    that the runtime is executing.
    """
    if LINUX_KERNEL_PROC.match(commandline):
        return commandline

    if OSX_PARENTHESIZED_PROC.match(commandline):
        return commandline

    command = os.path.basename(to_array(commandline)[0])

    command_split = command.split(".")
    if len(command_split) > 1:
        if len(command_split[-1]) > 4:
            # Pretend all the dots are a kind of path and go for the last
            # part only
            command = command_split[-1]
        else:
            # Assume last part is a file suffix (like ".exe") and take the
            # next to last part
            command = command_split[-2]

    if command in ['python', 'Python']:
        return get_python_command(commandline)

    return command


def get_python_command(commandline):
    array = to_array(commandline)
    python = os.path.basename(array[0])
    if len(array) == 1:
        return python

    if not array[1].startswith('-'):
        return os.path.basename(array[1])

    if len(array) > 2:
        if array[1] == '-m' and not array[2].startswith('-'):
            return os.path.basename(array[2])

    return python
