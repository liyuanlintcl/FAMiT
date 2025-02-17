import bench.taint as taint


def good(cond):
    source = "safe"
    match cond:
        case 1:
            pass
        case 2:
            pass
        case _:
            source = taint.source()
    if cond == 2 or cond == 1:
        taint.sink(source)
