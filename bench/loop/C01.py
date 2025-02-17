import bench.taint as taint


def good():
    s = taint.source()
    count = 0
    for i in range(10):
        count += i
    if count < 10:
        taint.sink(s)


def bad():
    s = taint.source()
    count = 0
    for i in range(10):
        count += i
    if count > 10:
        taint.sink(s)
