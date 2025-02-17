import bench.taint as taint


def good(x):
    source = taint.safe()
    a = [0] * 2
    cond = True
    try:
        a[x] = 1
    except IndexError:
        source = taint.source()
        cond = False
    if cond or a[0] ^ a[1]:
        taint.sink(source)


def bad(x):
    source = taint.safe()
    a = [0] * 2
    cond = True
    try:
        a[x] = 1
    except IndexError:
        source = taint.source()
        cond = False
    if not cond and not a[0] ^ a[1]:
        taint.sink(source)
