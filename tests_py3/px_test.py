import sys

from px import px
from px import px_processinfo
from unittest.mock import patch

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
    assert first_print_arg.startswith('1.')

@patch("px.px_processinfo.print_pid_info")
def test_cmdline_pid(mock):
    px._main(['px', '1235'])

    mock.assert_called_once()
    # First arg is a file descriptor that changes on every invocation, check the
    # PID arg only.
    assert mock.call_args.args[1] == 1235


# FIXME: Test 'px root'

# FIXME: Test just 'px'
