import bench.taint as taint


def good():
    s = taint.source()
    p = f(3)
    if p > 10:
        taint.sink(s)


def bad():
    s = taint.source()
    p = f(3)
    if p > 2:
        taint.sink(s)


def f(n):
    if n <= 0:
        return 0
    return n + f(n - 1)
