import bench.taint as taint


class A:
    @staticmethod
    def cond(cond):
        return cond


class B(A):
    def good(self, cond):
        source = taint.safe() if cond else taint.source()
        cond = self.cond(cond)
        if cond:
            taint.sink(source)
