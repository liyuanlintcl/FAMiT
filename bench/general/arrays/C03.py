import bench.taint as taint


def good1():
    s = taint.source()
    arr = [0] * 1 + [1] * 2 + [2] * 3
    if arr[0] == 1:
        taint.sink(s)


def good2():
    s = taint.source()
    arr = [0] * 1 + [1] * 2 + [2] * 3
    if arr[3] == 1:
        taint.sink(s)


def bad1():
    s = taint.source()
    arr = [0] * 1 + [1] * 2 + [2] * 3
    if arr[1] == 1:
        taint.sink(s)


def bad2():
    s = taint.source()
    arr = [0] * 1 + [1] * 2 + [2] * 3
    if arr[2] == 1:
        taint.sink(s)
