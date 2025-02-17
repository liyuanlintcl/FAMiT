import bench.taint as taint


def bad(cond):
    source = "safe"
    match cond:
        case 1:
            source = taint.source()
        case 2:
            source = "2"
    if cond == 1:
        taint.sink(source)


def good(cond):
    source = "safe"
    match cond:
        case 1:
            source = taint.source()
        case 2:
            source = "2"
    if cond != 1:
        taint.sink(source)
