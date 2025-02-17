import bench.taint as taint


# 等比数列求和
def good(a: float, q: float, n: int):
    inf = float('inf')
    assert -inf < a < inf
    assert -inf < q < inf
    assert n >= 0
    s = taint.source()
    count = 0
    for i in range(n):
        count += a
        a *= q
    result = q != 1 and q != 0 and abs(count - a * (1 - q ** n) / (1 - q)) > 1e-5
    if result:
        taint.sink(s)
