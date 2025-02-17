import bench.taint as taint


# 等差数列求和
def good(a: float, d: float, n: int):
    inf = float('inf')
    assert -inf < a < inf
    assert -inf < d < inf
    assert n >= 0
    s = taint.source()
    count = 0
    for i in range(n):
        count += a
        a += d
    result = abs(count - (a + (a + (n - 1) * d)) * n / 2) > 1e-5
    if result:
        taint.sink(s)
