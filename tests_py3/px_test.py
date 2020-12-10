import sys

from px import px
from px import px_process
from px import px_terminal
from px import px_processinfo

from unittest.mock import patch

from typing import List

@patch('px.px.install')
def test_cmdline_install(mock):
    args = ['px', '--install']
    px._main(args)
    mock.assert_called_once_with(args)

@patch("px.px_top.top")
def test_cmdline_top(mock):
    px._main(['px', '--top'])
    mock.assert_called_once()

@patch("px.px_top.top")
def test_cmdline_ptop(mock):
    px._main(['ptop'])
    mock.assert_called_once()

@patch("builtins.print")
def test_cmdline_help(mock):
    px._main(['px', '--help'])
    mock.assert_called_once_with(px.__doc__)

@patch("builtins.print")
def test_cmdline_version(mock):
    px._main(['px', '--version'])
    mock.assert_called_once()

    first_print_arg: str = mock.call_args.args[0]
    assert first_print_arg

@patch("px.px_processinfo.print_pid_info")
def test_cmdline_pid(mock):
    px._main(['px', '1235', '--no-pager'])

    mock.assert_called_once()
    print(mock)
    print(mock.call_args)
    print(mock.call_args.args)
    # First arg is a file descriptor that changes on every invocation, check the
    # PID arg only.
    assert mock.call_args.args[1] == 1235

@patch("px.px_terminal.to_screen_lines")
def test_cmdline_filter(mock):
    px._main(['px', 'root', '--no-pager'])

    mock.assert_called_once()
    print(mock)
    print(mock.call_args)
    print(mock.call_args.args)
    processes: List[px_process.PxProcess] = mock.call_args.args[0]

    # This assumes something is running as root. We can assume that, right?
    assert len(processes) > 0

    # All listed processes must match
    for process in processes:
        assert process.match('root')

@patch("px.px_terminal.to_screen_lines")
def test_cmdline_list_all_processes(mock):
    px._main(['px'])

    mock.assert_called_once()
    processes: List[px_process.PxProcess] = mock.call_args.args[0]

    # We are running, and something started us, so this list must not be empty
    assert len(processes) > 0
