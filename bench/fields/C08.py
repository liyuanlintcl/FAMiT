import bench.taint as taint


class C:
    def __init__(self):
        self.x = None

    def get(self):
        return self.x

    def set(self, x):
        self.x = x


def good(cond):
    c = C()
    source = taint.safe()
    if not cond:
        source = taint.source()
    c.set(cond)
    if c.get():
        taint.sink(source)
