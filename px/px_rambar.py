import sys

from . import px_process

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import List  # NOQA
    from six import text_type  # NOQA


def rambar(ram_bar_length, processes):
    # type: (int, List[px_process.PxProcess]) -> text_type
    return ram_bar_length * u"#"
