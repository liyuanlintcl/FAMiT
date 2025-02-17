import bench.taint as taint


class Static:
    cond = True

    @classmethod
    def turnOff(cls):
        cls.cond = False

    @classmethod
    def turnOn(cls):
        cls.cond = True


def good():
    source = taint.source()
    Static.turnOff()
    if Static.cond:
        taint.sink(source)


def bad():
    source = taint.source()
    Static.turnOn()
    if Static.cond:
        taint.sink(source)
