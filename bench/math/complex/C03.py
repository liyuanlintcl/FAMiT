import bench.taint as taint


# 基本不等式
def good(a: float, b: float):
    inf = float('inf')
    assert 0 < a < inf
    assert 0 < b < inf
    s = taint.source()
    H = 2 / (1 / a + 1 / b)
    G = (a * b) ** 0.5
    A = (a + b) / 2
    Q = ((a ** 2 + b ** 2) / 2) ** 0.5
    result = H <= G <= A <= Q
    if not result:
        taint.sink(s)
