import bench.taint as taint


def addOne(x):
    return x + 1


def good():
    x = 0
    source = taint.source()
    if addOne(x) != 1:
        taint.sink(source)


def bad():
    x = 1
    source = taint.source()
    if addOne(x) == 2:
        taint.sink(source)
