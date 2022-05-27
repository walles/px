from typing import Tuple


def bytes_to_strings(current_bytes_count: int, max_bytes_count: int) -> Tuple[str, str]:
    """
    Turn byte counts into strings like "14MB" / "16MB". Both strings will have
    the same unit, and the unit is based on the max_bytes_count value.

    Ref: https://github.com/walles/px/issues/97
    """
    KB = 1024**1
    MB = 1024**2
    GB = 1024**3
    TB = 1024**4

    unit = "B"
    divisor = 1
    if max_bytes_count < 7 * KB:
        pass
    elif max_bytes_count < 7 * MB:
        unit = "KB"
        divisor = KB
    elif max_bytes_count < 7 * GB:
        unit = "MB"
        divisor = MB
    elif max_bytes_count < 7 * TB:
        unit = "GB"
        divisor = GB
    else:
        unit = "TB"
        divisor = TB

    current_str = str(int(round(float(current_bytes_count) / divisor))) + unit
    max_str = str(int(round(float(max_bytes_count) / divisor))) + unit

    return (current_str, max_str)
