import re
import os
import random
import datetime

from px import px_file
from px import px_process
from px import px_ipc_map

import dateutil.parser

from typing import MutableMapping
from typing import Optional
from typing import List

# An example time string that can be produced by ps
TIMESTRING = "Mon Mar  7 09:33:11 2016"
TIMEZONE = datetime.datetime.now(datetime.timezone.utc).astimezone().tzinfo
TIME = dateutil.parser.parse(TIMESTRING).replace(tzinfo=TIMEZONE)


def load(sample_file_name: str) -> str:
    my_dir = os.path.dirname(__file__)
    full_path = os.path.join(my_dir, sample_file_name)
    with open(full_path, encoding="utf-8") as sample_file:
        return sample_file.read()


def spaces(at_least=1, at_most=3):
    return " " * random.randint(at_least, at_most)


def local_now():
    return datetime.datetime.now().replace(tzinfo=TIMEZONE)


def create_process(
    pid=47536,
    ppid=1234,
    rss_kb=12345,
    timestring=TIMESTRING,
    uid=0,
    cpuusage="0.0",
    cputime="0:00.03",
    mempercent="0.0",
    commandline="/usr/sbin/cupsd -l",
    now=local_now(),
) -> px_process.PxProcess:
    psline = (
        spaces(at_least=0)
        + str(pid)
        + spaces()
        + str(ppid)
        + spaces()
        + str(rss_kb)
        + spaces()
        + timestring
        + spaces()
        + str(uid)
        + spaces()
        + cpuusage
        + spaces()
        + cputime
        + spaces()
        + mempercent
        + spaces()
        + commandline
    )

    return px_process.ps_line_to_process(psline, now)


def create_file(
    filetype: str,
    name: str,
    device: Optional[str],
    pid: int,
    access: Optional[str] = None,
    inode: Optional[str] = None,
    fd: Optional[int] = None,
    fdtype: Optional[str] = None,
):
    # type (...) -> px_file.PxFile

    # Remove leading [] group from name if any
    match = re.match(r"(\[[^]]*\] )?(.*)", name)
    assert match
    name = match.group(2)

    file = px_file.PxFile(pid, filetype)
    file.name = name

    file.device = device
    file.access = access
    file.inode = inode
    file.fd = fd
    file.fdtype = fdtype
    return file


def create_ipc_map(
    pid: int, all_files: List[px_file.PxFile], is_root: bool = False
) -> px_ipc_map.IpcMap:
    """Wrapper around IpcMap() so that we can test it"""
    pid2process: MutableMapping[int, px_process.PxProcess] = {}
    for file in all_files:
        if file.pid in pid2process:
            continue
        pid2process[file.pid] = create_process(pid=file.pid)
    if pid not in pid2process:
        pid2process[pid] = create_process(pid=pid)

    processes = list(pid2process.values())
    random.shuffle(processes)

    process = pid2process[pid]

    return px_ipc_map.IpcMap(process, all_files, processes, is_root)


def fake_callchain(*args: str) -> px_process.PxProcess:
    procs = []
    for arg in args:
        procs.append(create_process(commandline=arg))

    parent = None
    last_proc = None
    for proc in procs:
        proc.parent = parent
        parent = proc
        last_proc = proc

    assert last_proc is not None
    return last_proc
