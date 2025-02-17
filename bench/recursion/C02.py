import bench.taint as taint


def good():
    s = taint.source()
    p = g(3)
    if p > 15:
        taint.sink(s)


def bad():
    s = taint.source()
    p = g(3)
    if p < 15:
        taint.sink(s)


def f(n):
    if n <= 0:
        return 2
    return n + g(n - 1)


def g(n):
    if n <= 0:
        return 1
    return f((n + 1) / 2) * n
