import bench.taint as taint


def good(a, b, c, d, e):
    source = taint.source()
    result = ((a > b) and (c < d) and (e >= 0)) and ((a <= b) and (c >= d) and e < 0)
    if result:
        taint.sink(source)
