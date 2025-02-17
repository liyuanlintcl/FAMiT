import bench.taint as taint


def good(a, b, c):
    source = taint.source()
    cond = ((a or b) and (not a or c)) and ((not b or not c) or (a and not c)) and (not a or b or not c) and (b and c)
    if cond:
        taint.sink(source)
        