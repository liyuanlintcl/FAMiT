import bench.taint as taint


def good(a, b):
    source = "safe"
    if a:
        source = "a"
    elif b:
        source = taint.source()

    if a:
        taint.source(source)

    if not b:
        taint.sink(source)

