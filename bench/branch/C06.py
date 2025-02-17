import bench.taint as taint


def good(a, b, c):
    source = "safe"
    if a:
        if b:
            if c:
                source = taint.source("abc")
            else:
                source = "ab!c"
        elif c:
            source = "a!bc"
        else:
            source = taint.source("a!b!c")
    elif b:
        if c:
            source = "!abc"
        else:
            source = taint.source("!ab!c")
    elif c:
        source = taint.source("!a!bc")
    else:
        source = "!a!b!c"

    if not a ^ b ^ c:
        taint.sink(source)


def bad(a, b, c):
    source = "safe"
    if a:
        if b:
            if c:
                source = taint.source("abc")
            else:
                source = "ab!c"
        elif c:
            source = "a!bc"
        else:
            source = taint.source("a!b!c")
    elif b:
        if c:
            source = "!abc"
        else:
            source = taint.source("!ab!c")
    elif c:
        source = taint.source("!a!bc")
    else:
        source = "!a!b!c"

    if a ^ b ^ c:
        taint.sink(source)

