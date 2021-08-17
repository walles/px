def cached(size=200):
    cache = {}
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
