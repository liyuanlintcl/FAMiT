import bench.taint as taint


class Base:
    def __init__(self):
        self.x = 0

    def set(self, x):
        self.x = x

    def get(self):
        return self.x


class A(Base):
    def set(self, x):
        self.x = x + 1


class B(Base):
    def set(self, x):
        self.x = x - 1

    def __init__(self):
        super().__init__()
        self.x = 1


class C(A, B):
    def f(self):
        return self


def good1():
    source = taint.source()
    c = C()
    if c.get() == 0:
        taint.sink(source)


def good2():
    source = taint.source()
    c = C()
    c.set(1)
    if c.get() == 1 or c.get() == 0:
        taint.sink(source)


def bad1():
    source = taint.source()
    c = C()
    if c.get() == 1:
        taint.sink(source)


def bad2():
    source = taint.source()
    c = C()
    c.set(1)
    if c.get() == 2:
        taint.sink(source)
