import bench.taint as taint


class C06:
    def __init__(self):
        self.cond = None

    def reachSink(self, source):
        if self.cond:
            taint.sink(source)

    def good(self):
        source = taint.source()
        self.cond = False
        self.reachSink(source)

    def bad(self):
        source = taint.source()
        self.cond = True
        self.reachSink(source)
