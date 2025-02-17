import bench.taint as taint


def b1(x):
    if x < -1:
        s = taint.source()
        s = b2(s)
    else:
        s = taint.safe()
    if x < 0:
        s = taint.source()
    s = b2(s)
    return s


def b2(s):
    t = s
    return t


def f1(x, s):
    s = f2(s)
    if x < 1:
        taint.sink(s)
    else:
        s = f2(s)
        if x < 2:
            taint.sink(s)
        else:
            s = taint.safe()


def f2(s):
    y = s
    return y


def good(i, j):
    if i < -2 and 2 <= j <= 3:
        s = b1(i)
        f1(j, s)
