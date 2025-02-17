import bench.taint as taint


class A:
    a = True


def reachSink(cond, source):
    if cond:
        taint.sink(source)


def good1():
    source = taint.source()
    A.a = False
    a = A()
    reachSink(a.a, source)


def bad1():
    source = taint.source()
    a = A()
    reachSink(a.a, source)


def good2():
    source = taint.source()
    a = A()
    a.a = False
    reachSink(a.a, source)


def good3():
    source = taint.source()
    a = A()
    a.a = False
    A.a = True
    reachSink(a.a, source)


def bad2():
    source = taint.source()
    a = A()
    b = A()
    a.a = True
    A.a = False
    reachSink(not b.a and a.a, source)


def good4():
    source = taint.source()
    a = A()
    A.b = False
    reachSink(a.b, source)


def bad3():
    source = taint.source()
    a = A()
    A.b = True
    reachSink(a.b, source)
