import bench.taint as taint


def good():
    s = taint.source()
    count = 0
    i = 0
    while i < 10:
        i += 1
        count += i
    if count < 10:
        taint.sink(s)


def bad():
    s = taint.source()
    count = 0
    i = 0
    while i < 10:
        i += 1
        count += i
    if count > 10:
        taint.sink(s)
