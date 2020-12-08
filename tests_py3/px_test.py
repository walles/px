import sys

from px import px
from unittest.mock import patch

def test_main():
    args = ['px', '--install']
    with patch("px.px.install") as install_mock:
        px._main(args)
        install_mock.assert_called_once_with(args)

    with patch("px.px_top.top") as top_mock:
        px._main(['px', '--top'])
        top_mock.assert_called_once()

    with patch("px.px_top.top") as top_mock:
        px._main(['ptop'])
        top_mock.assert_called_once()

    with patch("builtins.print") as print_mock:
        px._main(['px', '--help'])

        print_mock.assert_called_once_with(px.__doc__)

    # FIXME: Test --version

    # FIXME: Test 'px 1'

    # FIXME: Test 'px root'

    # FIXME: Test just 'px'

