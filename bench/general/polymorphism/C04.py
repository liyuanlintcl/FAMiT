import bench.taint


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


def good(cond):
    base = A if cond else B
    base_instance = base()
    super(base, base_instance).set(1)
    source = bench.taint.source()
    if base_instance.get() != 1:
        bench.taint.sink(source)


def bad(cond):
    base = A if cond else B
    base_instance = base()
    super(base, base_instance).set(1)
    source = bench.taint.source()
    if base_instance.get() == 1:
        bench.taint.sink(source)


