import sys

from typing import TypeVar, Callable, Any
if sys.version_info.major >= 3:
    # For mypy PEP-484 static typing validation
    from typing import Dict, Tuple, Callable  # NOQA


F = TypeVar('F', bound=Callable[..., Any])


def cached(size=200):
    # type: (int) -> Callable[[F], F]
    cache = {}  # type: Dict[Tuple, Any]
    def decorator(function):
        def wrapper(*args, **kwargs):
            args_tuple = tuple(args)
            if args_tuple in cache:
                return cache[args_tuple]

            result = function(*args, **kwargs)

            if len(cache) > size:
                cache.clear()
            cache[args_tuple] = result

            return result
        return wrapper
    return decorator
