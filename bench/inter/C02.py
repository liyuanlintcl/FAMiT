import bench.taint as taint


class C:
    def __init__(self):
        self.x = None
        self.s = None


def bad(i):
    a = C()
    b = C()
    if i > 0:
        a.s = taint.source()
        a.x = 1
    b.s = taint.safe()
    b.x = i
    c = a if i > 0 else b
    reachSink(c)


def good(i):
    a = C()
    b = C()
    if i > 0:
        a.s = taint.source()
        a.x = 1
    b.s = taint.safe()
    b.x = i
    c = a if i <= 0 else b
    reachSink(c)


def reachSink(c):
    if c.x > 0:
        taint.sink(c.s)
