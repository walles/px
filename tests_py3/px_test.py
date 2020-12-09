import sys

from px import px
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

# FIXME: Test 'px 1'

# FIXME: Test 'px root'

# FIXME: Test just 'px'
