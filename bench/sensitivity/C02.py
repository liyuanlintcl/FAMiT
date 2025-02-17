import bench.taint as taint


class Handle:
    def __init__(self, x, s):
        self.x = x
        self.s = s

    def __enter__(self):
        self.s = taint.safe(self.s)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.x > 0:
            taint.sink(self.s)


def good():
    source = taint.source()
    with Handle(0, source) as handle:
        taint.sink(handle.s)
        handle.s = taint.source()


def bad1():
    source = taint.source()
    with Handle(1, source) as handle:
        taint.sink(handle.s)
        handle.s = taint.source()


def bad2():
    source = taint.safe()
    with Handle(1, source) as handle:
        taint.sink(handle.s)
        handle.s = taint.source()
