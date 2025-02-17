from bench import taint


def my_decorator(func):
    def wrapper(*args, **kwargs):
        safe_args = [taint.safe(arg) for arg in args]
        safe_kwargs = {taint.safe(k): taint.safe(v) for k, v in kwargs.items()}
        return func(*safe_args, **safe_kwargs)

    return wrapper


@my_decorator
def safe_reach_to_sink(source):
    return taint.sink(source)


def good():
    s = taint.source()
    safe_reach_to_sink(s)
