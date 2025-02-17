import bench.taint as taint


def f(x, s):
    if x < -1:
        taint.sink(s)
    else:
        s = taint.safe()
    g(x, s)


def g(x, s):
    if x < 5:
        taint.sink(s)


def good():
    s = taint.source()
    f(3, s)


def bad():
    s = taint.source()
    f(-2, s)
