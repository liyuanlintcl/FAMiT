import bench.taint as taint


def good(a, b, cond):
    s = taint.source()
    a.x = 5
    b.x = 6
    c = a if cond else b
    if c.x > 20:
        taint.sink(s)


def bad(a, b, cond):
    s = taint.source()
    a.x = 5
    b.x = 6
    c = a if cond else b
    if c.x < 20:
        taint.sink(s)

