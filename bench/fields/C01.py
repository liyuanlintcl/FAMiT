import bench.taint as taint


def good(a):
    s = taint.source()
    a.x = 0
    if a.x > 10:
        taint.sink(s)
