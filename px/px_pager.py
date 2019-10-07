import os
import threading
import subprocess

from . import px_processinfo

if False:
    # For mypy PEP-484 static typing validation
    import logging               # NOQA
    from . import px_process     # NOQA
    from typing import List      # NOQA
    from typing import Optional  # NOQA


def _pump_info_to_fd(fileno, process, processes, log):
    # type: (int, px_process.PxProcess, List[px_process.PxProcess], logging.Logger) -> None
    try:
        px_processinfo.print_process_info(log, fileno, process, processes)
        os.close(fileno)
    except Exception:
        # Logging exceptions on warning level will make them visible to somebody
        # who changes the LOGLEVEL in px.py, but not to ordinary users.
        #
        # Getting some exceptions may or may not be benign if the user closes
        # the pager before we're done writing to its stdin pipe.

        # Got exc_info from: https://stackoverflow.com/a/193153/473672
        log.warning("Failed pumping process info into pager", exc_info=True)


# From: https://stackoverflow.com/a/377028/473672
def which(program):
    # type: (Optional[str]) -> Optional[str]
    if not program:
        return None

    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None


def to_command_line(spec):
    # type: (Optional[str]) -> Optional[List[str]]
    if not spec:
        return None

    split_spec = spec.split()
    arg0 = which(split_spec[0])
    if not arg0:
        # Not found
        return None

    return [arg0] + split_spec[1:]


def launch_pager():
    env = os.environ.copy()

    # Prevent --quit-if-one-screen, we always want a pager
    env['LESS'] = ''

    pager_cmd = to_command_line(env.get('PAGER', None))
    if not pager_cmd:
        # Prefer moar: https://github.com/walles/moar
        pager_cmd = to_command_line('moar')
    if not pager_cmd:
        pager_cmd = to_command_line('less')

    # FIXME: What should we do if we don't find anything to page with?
    assert pager_cmd is not None

    if pager_cmd[0].split(os.sep)[-1] == 'less':
        # Prevent --quit-if-one-screen, we always want a pager
        pager_cmd = pager_cmd[0:1]

    return subprocess.Popen(pager_cmd, stdin=subprocess.PIPE, env=env)


def page_process_info(process, processes, log):
    # type: (px_process.PxProcess, List[px_process.PxProcess], logging.Logger) -> None

    pager = launch_pager()
    pager_stdin = pager.stdin
    assert pager_stdin is not None

    # Do this in a thread to avoid problems with pipe buffers filling up and blocking
    info_thread = threading.Thread(
        target=_pump_info_to_fd,
        args=(pager_stdin.fileno(), process, processes, log))
    info_thread.setDaemon(True)  # Terminating ptop while this is running is fine
    info_thread.start()

    pagerExitcode = pager.wait()
    if pagerExitcode != 0:
        log.warn("Pager exited with code %d", pagerExitcode)

    # FIXME: Maybe join info_thread here as well to ensure we aren't still pumping before returning?
    # This could possibly prevent https://github.com/walles/px/issues/67
