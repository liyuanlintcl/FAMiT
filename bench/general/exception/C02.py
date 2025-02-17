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
    if cond or 0 <= x < 2:
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
    if not cond and x >= 2 or x < 0:
        taint.sink(source)
