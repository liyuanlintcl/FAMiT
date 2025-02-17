import bench.taint as taint


def good1():
    s = taint.source()
    arr = [1, 2, 3]
    arr.append(2)
    if arr[-1] == 3:
        taint.sink(s)


def good2():
    s = taint.source()
    arr = [1, 2, 3]
    arr.pop()
    if arr[-1] == 3:
        taint.sink(s)


def good3():
    s = taint.source()
    arr = [1, 2, 3]
    arr.pop()
    arr.append(2)
    arr.append(3)
    if arr[2] == 3:
        taint.sink(s)


def bad1():
    s = taint.source()
    arr = [1, 2, 3]
    arr.append(2)
    if arr[-1] == 2:
        taint.sink(s)


def bad2():
    s = taint.source()
    arr = [1, 2, 3]
    arr.pop()
    if arr[-1] == 2:
        taint.sink(s)


def bad3():
    s = taint.source()
    arr = [1, 2, 3]
    arr.pop()
    arr.append(2)
    arr.append(3)
    if arr[2] == 2:
        taint.sink(s)
