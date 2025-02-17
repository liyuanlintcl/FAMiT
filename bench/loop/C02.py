import bench.taint as taint


def good():
    s = taint.source()
    count = 0
    for i in range(10):
        count += 1
        if count > 5:
            break
    if count < 3:
        taint.sink(s)


def bad():
    s = taint.source()
    count = 0
    for i in range(10):
        count += 1
        if count > 5:
            break
    if count >= 3:
        taint.sink(s)
