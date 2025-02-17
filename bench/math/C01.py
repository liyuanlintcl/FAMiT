import bench.taint as taint


def good(a, b):
    source = taint.source()
    cond1 = a and b
    cond2 = not (a or b)
    result = and_(cond1, cond2)
    if result:
        taint.sink(source)


def and_(a, b):
    return a and b
