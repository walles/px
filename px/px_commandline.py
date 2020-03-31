"""Extract information from command lines"""

import re
import sys
import os.path

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type  # NOQA
    from typing import List    # NOQA


# Match "[kworker/0:0H]", no grouping
LINUX_KERNEL_PROC = re.compile(u"^\\[[^/ ]+/?[^/ ]+\\]$")

# Match "(python2.7)", no grouping
OSX_PARENTHESIZED_PROC = re.compile(u"^\\([^()]+\\)$")


def to_array(commandline):
    # type: (text_type) -> List[text_type]
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


def is_human_friendly(command):
    # type: (text_type) -> bool
    """
    AKA "Does this command contain any capital letters?"
    """
    for char in command:
        if char.isupper():
            return True
    return False


def get_app_name_prefix(commandline):
    # type: (text_type) -> text_type
    """
    On macOS, get which app this command is part of.
    """
    command_with_path = to_array(commandline)[0]
    command = os.path.basename(command_with_path)
    for part in command_with_path.split("/"):
        if '.' not in part:
            continue

        name, suffix = part.rsplit(".", 1)
        if suffix not in ["app", "framework"]:
            continue

        if name == command:
            continue

        return name + "/"

    return ""


def get_command(commandline):
    # type: (text_type) -> text_type
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

    if command == "ruby":
        # Switches list inspired by ruby 2.3.7p456 --help output
        return get_generic_script_command(commandline, [
            '-a',
            '-d',
            '--debug',
            '--disable',
            '-l',
            '-n',
            '-p',
            '-s',
            '-S',
            '-v',
            '--verbose',
            '-w',
            '-W0',
            '-W1',
            '-W2'
        ])

    if command == "sudo":
        return get_sudo_command(commandline)

    if command == "node":
        return get_generic_script_command(commandline, ["--max_old_space_size"])

    if command in ["bash", "sh", "perl"]:
        return get_generic_script_command(commandline)

    app_name_prefix = get_app_name_prefix(commandline)
    if is_human_friendly(command):
        # Already human friendly, prefer keeping it short
        app_name_prefix = ""

    if len(command) < 25:
        return app_name_prefix + command

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

    return app_name_prefix + command


def get_python_command(commandline):
    # type: (text_type) -> text_type
    array = to_array(commandline)
    array = list(filter(lambda s: s, array))

    # Ignore some switches, list inspired by 'python2.7 --help'
    IGNORE_SWITCHES = [
        '-b', '-bb',
        '-B',
        '-d',
        '-E',
        '-i',
        '-O',
        '-OO',
        '-R',
        '-s',
        '-S',
        '-t', '-tt',
        '-u',
        '-v',
        '-Werror',
        '-x',
        '-3'
    ]
    while len(array) > 1 and array[1] in IGNORE_SWITCHES:
        del array[1]

    python = os.path.basename(array[0])
    if len(array) == 1:
        return python

    if not array[1].startswith('-'):
        return os.path.basename(array[1])

    if len(array) > 2:
        if array[1] == '-m' and not array[2].startswith('-'):
            return os.path.basename(array[2])

    return python


def get_sudo_command(commandline):
    # type: (text_type) -> text_type
    without_sudo = commandline[5:].strip()
    if not without_sudo:
        return "sudo"

    if without_sudo.startswith('-'):
        # Give up on options
        return "sudo"

    return "sudo " + get_command(without_sudo)


def prettify_fully_qualified_java_class(class_name):
    # type: (text_type) -> text_type
    split = class_name.split('.')
    if len(split) == 1:
        return split[-1]

    if split[-1] == 'Main':
        # Attempt to make "Main" class names more meaningful
        return split[-2] + '.' + split[-1]

    return split[-1]


def get_java_command(commandline):
    # type: (text_type) -> text_type
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
            if component.startswith('-agentlib:'):
                continue
            if component.startswith('-javaagent:'):
                continue
            if component == "-server":
                continue
            if component == "-noverify":
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


def get_generic_script_command(commandline, ignore_switches=[]):
    # type: (text_type, List[text_type]) -> text_type
    array = to_array(commandline)

    while len(array) > 1 and array[1].split("=")[0] in ignore_switches:
        del array[1]

    vm = os.path.basename(array[0])
    if len(array) == 1:
        return vm

    if array[1].startswith('-'):
        # This is some option, we don't do options
        return vm

    return os.path.basename(array[1])
