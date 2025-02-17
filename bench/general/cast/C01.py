import bench.taint as taint


def good(d):
    s = taint.source()
    if -100. < d < 100.:
        p = int(d)
        if d < p - 1 or d > p + 1:
            taint.sink(s)
