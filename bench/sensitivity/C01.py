import bench.taint as taint


class A:
    def wrapper(self, x):
        return self.id(x)

    @staticmethod
    def id(x):
        return x


def good(x):
    a = A()
    source = taint.safe()
    if a.wrapper(0) == 1:
        source = taint.source()
    if a.wrapper(x) == x:
        taint.sink(source)


def bad(x):
    a = A()
    source = taint.safe()
    if a.wrapper(0) == 0:
        source = taint.source()
    if a.wrapper(x) == x:
        taint.sink(source)

