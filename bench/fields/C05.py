import bench.taint as taint


class A:
    def __init__(self):
        self.b = None


class B:
    def __init__(self, x):
        self.x = x


def good(cond):
    source = taint.safe()
    if not cond:
        source = taint.source()
    a = A()
    a.b = B(cond)
    if a.b.x:
        taint.sink(source)


def bad(cond):
    source = taint.safe()
    if cond:
        source = taint.source()
    a = A()
    a.b = B(cond)
    if a.b.x:
        taint.sink(source)
