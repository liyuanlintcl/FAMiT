import bench.taint as taint


def f(x):
    s = None
    if x < -1:
        return taint.source()
    else:
        s = taint.safe()
    return g(x, s)


def g(x, s):
    if x < 5:
        return taint.source()
    return s


def good():
    s = f(6)
    taint.sink(s)


def bad():
    s = f(3)
    taint.sink(s)
