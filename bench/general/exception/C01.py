import bench.taint as taint


def good(x):
    source = taint.safe()
    a = [0] * 2
    cond = True
    try:
        a[x] = a[0]
    except IndexError:
        source = taint.source()
        cond = False
    if cond:
        taint.sink(source)


def bad(x):
    source = taint.safe()
    a = [0] * 2
    cond = True
    try:
        a[x] = a[0]
    except IndexError:
        source = taint.source()
        cond = False
    if not cond:
        taint.sink(source)
