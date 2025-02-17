import bench.taint as taint


# 斐波那契数列通项
def good(n: int):
    s = taint.source()
    result = n > 0 and isinstance(n, int) and abs(((1 + 5 ** 0.5) ** n - (1 - 5 ** 0.5) ** n) / 5 ** 0.5 - fib(n)) > 1e-5
    if not result:
        taint.sink(s)


def fib(n):
    if n <= 2:
        return 1
    return fib(n - 1) + fib(n - 2)
