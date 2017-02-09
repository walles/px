"""Extract information from command lines"""

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

    if command.startswith('python') or command == 'Python':
        return get_python_command(commandline)

    if command == "java":
        return get_java_command(commandline)

    if command in ["bash", "sh", "ruby", "perl", "node"]:
        return get_generic_script_command(commandline)

    if len(command) < 25:
        return command

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

    return command


def get_python_command(commandline):
    array = to_array(commandline)
    array = list(filter(lambda s: s, array))
    python = os.path.basename(array[0])
    if len(array) == 1:
        return python

    if not array[1].startswith('-'):
        return os.path.basename(array[1])

    if len(array) > 2:
        if array[1] == '-m' and not array[2].startswith('-'):
            return os.path.basename(array[2])

    return python


def prettify_fully_qualified_java_class(class_name):
    split = class_name.split('.')
    if len(split) == 1:
        return split[-1]

    if split[-1] == 'Main':
        # Attempt to make "Main" class names more meaningful
        return split[-2] + '.' + split[-1]

    return split[-1]


def get_java_command(commandline):
    array = to_array(commandline)
    java = os.path.basename(array[0])
    if len(array) == 1:
        return java

    state = "skip next"
    for component in array:
        if not component:
            # Skip all empties
            continue

        if state == "skip next":
            if component.startswith("-"):
                # Skipping switches doesn't make sense. We're lost, fall back to
                # just returning the command name
                return java
            state = "scanning"
            continue
        if state == "return next":
            if component.startswith("-"):
                # Returning switches doesn't make sense. We're lost, fall back
                # to just returning the command name
                return java
            return os.path.basename(component)
        elif state == "scanning":
            if component.startswith('-X'):
                continue
            if component.startswith('-D'):
                continue
            if component.startswith('-ea'):
                continue
            if component.startswith('-da'):
                continue
            if component == "-server":
                continue
            if component == "-cp" or component == "-classpath":
                state = "skip next"
                continue
            if component == '-jar':
                state = "return next"
                continue
            if component.startswith('-'):
                # Unsupported switch, give up
                return java
            return prettify_fully_qualified_java_class(component)
        else:
            raise ValueError("Unhandled state <{}> at <{}> for: {}".format(state, component, array))

    # We got to the end without being able to come up with a better name, give up
    return java


def get_generic_script_command(commandline):
    array = to_array(commandline)
    vm = os.path.basename(array[0])
    if len(array) == 1:
        return vm

    if array[1].startswith('-'):
        # This is some option, we don't do options
        return vm

    return os.path.basename(array[1])
