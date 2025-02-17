import bench.taint as taint


class A:
    def __init__(self):
        self.a = True


def reachSink(cond, source):
    if cond:
        taint.sink(source)


def bad():
    source = taint.source()
    a = A()
    A.a = False
    reachSink(a.a, source)


def good():
    source = taint.source()
    a = A()
    a.a = False
    A.a = True
    reachSink(a.a, source)



