import bench.taint as taint


def good(a, b):
    s = taint.source()
    result = (a - b >= 1) and (-a + b >= 1) and a >= 0 and b >= 0
    if result:
        taint.sink(s)
