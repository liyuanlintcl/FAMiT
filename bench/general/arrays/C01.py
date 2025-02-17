import bench.taint as taint


def getIndex():
    return 0


def good():
    s = taint.source()
    arr = [1, 2, 3, 4]
    if arr[getIndex()] == 2:
        taint.sink(s)


def bad():
    s = taint.source()
    arr = [1, 2, 3, 4]
    if arr[getIndex()] < 2:
        taint.sink(s)
