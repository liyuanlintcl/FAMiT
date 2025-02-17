import bench.taint as taint


def good(a, b):
    s = taint.source()
    a.x = 5
    b.x = 6
    if a.x + b.x > 20:
        taint.sink(s)


def bad(a, b):
    s = taint.source()
    a.x = 5
    b.x = 6
    if a.x + b.x < 20:
        taint.sink(s)

