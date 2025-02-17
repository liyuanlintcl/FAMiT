import bench.taint as taint


class C:
    def __init__(self):
        self.x = None
        self.s = None

    def reachSink(self, source):
        if self.x < 0:
            taint.sink(source)


def foo(c):
    x = c.x - 3


def good(i):
    a = C()
    b = a
    if i > 0:
        a.s = taint.source()
        a.x = i
    foo(a)
    b.reachSink(b.s)


def bad(i):
    a = C()
    b = a
    if i < 0:
        a.s = taint.source()
        a.x = i
    foo(a)
    b.reachSink(b.s)
