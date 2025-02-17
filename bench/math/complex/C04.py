import bench.taint as taint


# 线性规划
def good(a: float, b: float):
    s = taint.source()
    result = not (2 * a + b <= 10 and a + b <= 8 and b <= 7 and a >= 0 and b >= 0) or 4 * a + 3 * b > 26
    if not result:
        taint.sink(s)
