import bench.taint as taint


def good(cond):
    source = taint.source() if cond else "safe"
    if not cond:
        taint.sink(source)


def bad(cond):
    source = taint.source() if cond else "safe"
    if cond:
        taint.sink(source)


