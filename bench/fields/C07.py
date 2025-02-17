import bench.taint as taint


def good(a):
    source = taint.source()
    a.x = 0
    reachSink(a, source)


def reachSink(a, source):
    if a.x != 0:
        taint.sink(source)
