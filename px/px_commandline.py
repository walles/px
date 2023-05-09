"""Extract information from command lines"""

import re
import os.path
import logging

from typing import List, Optional

LOG = logging.getLogger(__name__)


# Match "[kworker/0:0H]", no grouping
LINUX_KERNEL_PROC = re.compile("^\\[[^/ ]+/?[^/ ]+\\]$")

# Match "(python2.7)", no grouping
OSX_PARENTHESIZED_PROC = re.compile("^\\([^()]+\\)$")

# Name of the Perl interpreter
PERL_BIN = re.compile("^perl[.0-9]*$")


def to_array(commandline: str) -> List[str]:
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
        merged_split[0:2] = [" ".join(merged_split[0:2])]

    return merged_split


def is_human_friendly(command: str) -> bool:
    """
    AKA "Does this command contain any capital letters?"
    """
    for char in command:
        if char.isupper():
            return True
    return False


def get_app_name_prefix(commandline: str) -> str:
    """
    On macOS, get which app this command is part of.
    """
    command_with_path = to_array(commandline)[0]
    command = os.path.basename(command_with_path)
    for part in command_with_path.split("/"):
        if "." not in part:
            continue

        name, suffix = part.rsplit(".", 1)
        if suffix not in ["app", "framework"]:
            continue

        if name == command:
            continue

        return name + "/"

    return ""


def try_clarify_electron(commandline: str) -> Optional[str]:
    for path_component in to_array(commandline)[0].split("/"):
        if path_component.endswith(".app"):
            return path_component[:-4]

    return None


def faillog(commandline: str, parse_result: Optional[str]) -> str:
    """
    If successful, just return the result. If unsuccessful log the problem and
    return the VM name.
    """
    if parse_result:
        return parse_result

    LOG.debug("Parsing failed, using fallback: <%s>", commandline)

    vm = os.path.basename(to_array(commandline)[0])
    return vm


def get_command(commandline: str) -> str:
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

    if command.startswith("python") or command == "Python":
        return faillog(commandline, get_python_command(commandline))

    if command == "Electron":
        clarified = try_clarify_electron(commandline)
        if clarified:
            return clarified

    if command == "java":
        return faillog(commandline, get_java_command(commandline))

    if command == "ruby":
        # Switches list inspired by ruby 2.3.7p456 --help output
        return faillog(
            commandline,
            get_generic_script_command(
                commandline,
                ignore_switches=[
                    "-a",
                    "-d",
                    "--debug",
                    "--disable",
                    #
                    # Quickfix for #74, better implementations welcome!
                    # https://github.com/walles/px/issues/74
                    "-Eascii-8bit:ascii-8bit",
                    #
                    "-l",
                    "-n",
                    "-p",
                    "-s",
                    "-S",
                    "-v",
                    "--verbose",
                    "-w",
                    "-W0",
                    "-W1",
                    "-W2",
                    "--",
                ],
            ),
        )

    if command == "sudo":
        return faillog(commandline, get_sudo_command(commandline))

    if command in [
        # NOTE: This list contains binaries that are mostly used with
        # subcommands. Scripts (like brew.rb) are handled in
        # get_generic_script_command().
        #
        # "gradle" and "mvn" are not handled at all, could be added to
        # get_java_command().
        "apt-get",
        "apt",
        "cargo",
        "docker",
        "docker-compose",
        "git",
        "go",
        "npm",
        "pip",
        "pip3",
        "rustup",
    ]:
        return faillog(commandline, get_with_subcommand(commandline))

    if command == "terraform":
        return faillog(
            commandline, get_with_subcommand(commandline, ignore_switches=["-chdir"])
        )

    if command == "node":
        return faillog(
            commandline,
            get_generic_script_command(
                commandline, ignore_switches=["--max_old_space_size"]
            ),
        )

    if command in ["bash", "sh"]:
        return faillog(commandline, get_generic_script_command(commandline))

    if PERL_BIN.match(command):
        return faillog(commandline, get_generic_script_command(commandline))

    app_name_prefix = get_app_name_prefix(commandline)
    if is_human_friendly(command):
        # Already human friendly, prefer keeping it short
        app_name_prefix = ""

    if len(command) < 25:
        return app_name_prefix + command

    command_split = command.split(".")
    if len(command_split) > 1:
        command_suggestion = ""
        if len(command_split[-1]) > 4:
            # Pretend all the dots are a kind of path and go for the last
            # part only
            command_suggestion = command_split[-1]
        else:
            # Assume last part is a file suffix (like ".exe") and take the
            # next to last part
            command_suggestion = command_split[-2]
        if len(command_suggestion) >= 5:
            # Good enough!
            command = command_suggestion

    return app_name_prefix + command


def get_python_command(commandline: str) -> Optional[str]:
    """Returns None if we failed to figure out the script name"""
    array = to_array(commandline)
    array = list(filter(lambda s: s, array))

    # Ignore some switches, list inspired by 'python2.7 --help'
    IGNORE_SWITCHES = [
        "-b",
        "-bb",
        "-B",
        "-d",
        "-E",
        "-i",
        "-O",
        "-OO",
        "-R",
        "-s",
        "-S",
        "-t",
        "-tt",
        "-u",
        "-v",
        "-Werror",
        "-x",
        "-3",
    ]
    while len(array) > 1 and array[1] in IGNORE_SWITCHES:
        del array[1]

    python = os.path.basename(array[0])
    if len(array) == 1:
        return python

    if not array[1].startswith("-"):
        return os.path.basename(array[1])

    if len(array) > 2:
        if array[1] == "-m" and not array[2].startswith("-"):
            return os.path.basename(array[2])

    return None


def get_sudo_command(commandline: str) -> Optional[str]:
    """Returns None if we failed to figure out the script name"""
    without_sudo = commandline[5:].strip()
    if not without_sudo:
        return "sudo"

    if without_sudo.startswith("-"):
        # Give up on options
        return None

    return "sudo " + get_command(without_sudo)


def prettify_fully_qualified_java_class(class_name: str) -> str:
    split = class_name.split(".")
    if len(split) == 1:
        return split[-1]

    if split[-1] == "Main":
        # Attempt to make "Main" class names more meaningful
        return split[-2] + "." + split[-1]

    return split[-1]


def get_java_command(commandline: str) -> Optional[str]:
    """Returns None if we failed to figure out the script name"""
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
                # Skipping switches doesn't make sense. We're lost.
                return None
            state = "scanning"
            continue
        if state == "return next":
            if component.startswith("-"):
                # Returning switches doesn't make sense. We're lost.
                return None
            return os.path.basename(component)
        if state == "scanning":
            if component.startswith("-X"):
                continue
            if component.startswith("-D"):
                continue
            if component.startswith("-ea"):
                continue
            if component.startswith("-da"):
                continue
            if component.startswith("-agentlib:"):
                continue
            if component.startswith("-javaagent:"):
                continue
            if component.startswith("--add-modules="):
                continue
            if component == "--add-modules":
                state = "skip next"
                continue
            if component.startswith("--add-opens="):
                continue
            if component == "--add-opens":
                state = "skip next"
                continue
            if component.startswith("--add-exports="):
                continue
            if component == "--add-exports":
                state = "skip next"
                continue
            if component.startswith("--add-reads="):
                continue
            if component == "--add-reads":
                state = "skip next"
                continue
            if component.startswith("--patch-module="):
                continue
            if component == "--patch-module":
                state = "skip next"
                continue
            if component == "-server":
                continue
            if component == "-noverify":
                continue
            if component in ("-cp", "-classpath"):
                state = "skip next"
                continue
            if component == "-jar":
                state = "return next"
                continue
            if component.startswith("-"):
                # Unsupported switch, give up
                return None
            return prettify_fully_qualified_java_class(component)

        raise ValueError(f"Unhandled state <{state}> at <{component}> for: {array}")

    # We got to the end without being able to come up with a better name, give up
    return None


def get_with_subcommand(
    commandline: str, ignore_switches: Optional[List[str]] = None
) -> Optional[str]:
    array = to_array(commandline)

    if ignore_switches is None:
        ignore_switches = []
    while len(array) > 1 and array[1].split("=")[0] in ignore_switches:
        del array[1]

    command = os.path.basename(array[0])
    if len(array) == 1:
        return command

    if array[1].startswith("-"):
        # Unknown option, help!
        return command

    return f"{command} {array[1]}"


def get_generic_script_command(
    commandline: str, ignore_switches: Optional[List[str]] = None
) -> Optional[str]:
    """Returns None if we failed to figure out the script name"""
    array = to_array(commandline)

    if ignore_switches is None:
        ignore_switches = []
    while len(array) > 1 and array[1].split("=")[0] in ignore_switches:
        del array[1]

    vm = os.path.basename(array[0])
    if len(array) == 1:
        return vm

    if array[1].startswith("-"):
        # Unknown option, help!
        return None

    script = os.path.basename(array[1])
    if len(array) == 2:
        # vm + script
        return script
    if script not in ["brew.rb", "yarn.js"]:
        return script
    script = os.path.splitext(script)[0]

    subcommand = array[2]
    if subcommand.startswith("-"):
        # Unknown option before the subcommand
        return script

    return f"{script} {subcommand}"
