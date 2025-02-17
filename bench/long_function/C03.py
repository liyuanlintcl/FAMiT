import bench.taint as taint


def func1(args):
    if args.a >= 100:
        return
    args.a += 1
    args.b = factorial(args.b)
    func2(args)


def func2(args):
    if args.a >= 100:
        return
    args.a += 2
    args.b = fibonacci(args.b)
    func3(args)


def func3(args):
    if args.a >= 100:
        return
    args.a += 3
    args.b = is_prime(args.b)
    func4(args)


def func4(args):
    if args.a >= 100:
        return
    args.a += 4
    args.b = sum_of_digits(args.b)
    func5(args)


def func5(args):
    if args.a >= 100:
        return
    args.a += 5
    args.b = reverse_number(args.b)
    func6(args)


def func6(args):
    if args.a >= 100:
        return
    args.a += 6
    args.b = power_of_two(args.b)
    func7(args)


def func7(args):
    if args.a >= 100:
        return
    args.a += 7
    args.b = palindrome(args.b)
    func8(args)


def func8(args):
    if args.a >= 100:
        return
    args.a += 8
    args.b = armstrong_number(args.b)
    func9(args)


def func9(args):
    if args.a >= 100:
        return
    args.a += 9
    args.b = gcd(args.a, args.b)
    func10(args)


def func10(args):
    if args.a >= 100:
        return
    args.a += 10
    args.b = fast_pow(args.a, args.b)
    func1(args)


def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n - 1)


def fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


def is_prime(n):
    if n <= 1:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True


def sum_of_digits(n):
    return sum((int(digit) for digit in str(n)))


def reverse_number(n):
    return int(str(n)[::-1])


def power_of_two(n):
    return 2 ** n


def palindrome(n):
    return str(n) == str(n)[::-1]


def armstrong_number(n):
    return n == sum((int(digit) ** 3 for digit in str(n)))


def gcd(a, b):
    while b:
        a, b = (b, a % b)
    return a


def fast_pow(a, b):
    res = 0
    pow_ = 1
    while b > 0:
        if b % 2 == 1:
            res += pow_
        pow_ *= a
    return res


def bad(args):
    source = taint.source()
    args.a = 0
    func1(args)
    if args.a == 110:
        taint.sink(source)


def good(args):
    source = taint.source()
    args.a = 0
    func1(args)
    if args.a != 110:
        taint.sink(source)
