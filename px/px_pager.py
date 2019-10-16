import os
import errno
import logging
import threading
import subprocess

from . import px_processinfo

if False:
    # For mypy PEP-484 static typing validation
    import logging               # NOQA
    from . import px_process     # NOQA
    from typing import List      # NOQA
    from typing import Optional  # NOQA

LOG = logging.getLogger(__name__)


def _pump_info_to_fd(with_fileno, process, processes):
    # FIXME: Type check first parameter using mypy protocols?
    # See: https://stackoverflow.com/a/56081214/473672

    # NOTE: The first parameter to this function *must* be *an object owning the fileno*,
    # not just the fileno itself. Otherwise the file will get closed when the fileno owner
    # goes out of scope in the main thread, and we'll be talking to a fileno which points
    # to who-knows-where.
    try:
        px_processinfo.print_process_info(with_fileno.fileno(), process, processes)
        with_fileno.close()
    except OSError as e:
        if e.errno == errno.EPIPE:
            # The user probably just exited the pager before we were done piping into it
            LOG.debug("Lost contact with pager, errno %d", e.errno)

            # FIXME: If an lsof instance was spawned by our px_processinfo.print_process_info()
            # call above (this is likely), we may want to kill that particular lsof instance.
            # It will use a bunch of CPU for some time, and we will never use its result anyway.
        else:
            LOG.warning("Unexpected OSError pumping process info into pager", exc_info=True)
    except Exception:
        # Logging exceptions on warning level will make them visible to somebody
        # who changes the LOGLEVEL in px.py, but not to ordinary users.
        #
        # Getting some exceptions may or may not be benign if the user closes
        # the pager before we're done writing to its stdin pipe.

        # Got exc_info from: https://stackoverflow.com/a/193153/473672
        LOG.warning("Failed pumping process info into pager", exc_info=True)


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


def page_process_info(process, processes):
    # type: (px_process.PxProcess, List[px_process.PxProcess]) -> None

    pager = launch_pager()
    pager_stdin = pager.stdin
    assert pager_stdin is not None

    # Do this in a thread to avoid problems with pipe buffers filling up and blocking
    info_thread = threading.Thread(
        target=_pump_info_to_fd,
        args=(pager_stdin, process, processes))
    info_thread.setDaemon(True)  # Terminating ptop while this is running is fine
    info_thread.start()

    pagerExitcode = pager.wait()
    if pagerExitcode != 0:
        LOG.warn("Pager exited with code %d", pagerExitcode)

    # FIXME: Maybe join info_thread here as well to ensure we aren't still pumping before returning?
    # This could possibly prevent https://github.com/walles/px/issues/67
