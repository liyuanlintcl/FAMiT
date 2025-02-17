import bench.taint as taint


def good(a, b):
    s = taint.source()
    c = (a - b) * (a + b)
    d = a & c
    e = c | d
    f = a % b
    f = ~f

    result = (-e + f >= 1) and (-e - f >= 1) and 0 <= e <= 100 and 0 <= f <= 100
    if result:
        taint.sink(s)


def bad(a, b, c, d, e, f):
    s = taint.source()
    result = ((a - b) * (a + b) > (e / f)) and ((a % b) == (c & d)) and ((a | b) != (c ^ d)) and ((a * b) == (c - d))
    if result:
        taint.sink(s)
