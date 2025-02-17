import bench.taint as taint


class A:
    @staticmethod
    def cond(cond):
        return cond


class B(A):
    @staticmethod
    def cond(cond):
        return not cond


def good(cond):
    a = A()
    b = B()
    source = taint.safe()
    if a.cond(cond):
        source = taint.source()
    if b.cond(cond):
        taint.sink(source)


def bad(cond):
    a = A()
    b = B()
    source = taint.safe()
    if a.cond(cond):
        source = taint.source()
    if b.cond(not cond):
        taint.sink(source)
