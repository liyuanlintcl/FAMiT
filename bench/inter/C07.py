import bench.taint as taint


def good(cond):
    source = taint.source()
    if cond == 0:
        reachSink(source, cond)


def reachSink(source, cond):
    if cond != 0:
        taint.sink(source)
