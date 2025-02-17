import bench.taint as taint


def bad1(a, b):
    source = "safe"
    if a or b:
        source = taint.source()
    if not a:
        taint.sink(source)


def bad2(a, b):
    source = "safe"
    if a or b:
        source = taint.source()
    if not b:
        taint.sink(source)


def good(a, b):
    source = "safe"
    if a or b:
        source = taint.source()
    if not a and not b:
        taint.sink(source)
