import bench.taint as taint


class A:
    @staticmethod
    def cond(cond):
        return not cond


class B(A):
    def bad(self, cond):
        source = taint.safe() if cond else taint.source()
        cond = self.cond(cond)
        if cond:
            taint.sink(source)
