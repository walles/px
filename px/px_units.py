import sys

if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from six import text_type  # NOQA


def bytes_to_string(bytes_count):
    # type: (int) -> text_type
    """
    Turn byte counts into strings like "14MB"
    """
    KB = 1024 ** 1
    MB = 1024 ** 2
    GB = 1024 ** 3
    TB = 1024 ** 4

    if bytes_count < 7 * KB:
        return str(bytes_count) + "B"

    if bytes_count < 7 * MB:
        return str(int(round(float(bytes_count) / KB))) + "KB"

    if bytes_count < 7 * GB:
        return str(int(round(float(bytes_count) / MB))) + "MB"

    if bytes_count < 7 * TB:
        return str(int(round(float(bytes_count) / GB))) + "GB"

    return str(int(round(float(bytes_count) / TB))) + "TB"
