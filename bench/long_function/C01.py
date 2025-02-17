import random
import bench.taint as taint


def f(b):
    if b < 0:
        return -f(-b)
    if b == 0:
        return 0
    if b == 1 or b == 2:
        return 1
    return f(b - 1) + f(b - 2)


def g(b):
    bits = []
    for i in range(4):
        bits.append(b % 10)
        b //= 10
    sorted(bits)
    return bits


def h(b):
    i = 2
    while i * i < b:
        if b % i == 0:
            return False
    return True


def func(args):
    args.a = 0
    b = 0
    if args.count:
        args.a += 1
        if b > 0:
            b = f(b)
        b += args.a
        if b < 0:
            b = 2 * f(b // 2)
        elif b == 0:
            b += f(0)
        else:
            b = f(2 * b) // 2
    if args.vote:
        args.a += 1
        if 0 < b < 10000:
            bits = g(b)
            if len(set(bits)) > 1:
                visited_number = []
                while b not in visited_number:
                    visited_number.append(b)
                    num_1 = 0
                    num_2 = 0
                    for i in range(4):
                        num_1 = num_1 * 10 + bits[4 - i]
                        num_2 = num_2 * 10 + bits[i]
                    b = num_1 - num_2
        elif b > 0:
            visited_number = []
            while b not in visited_number:
                visited_number.append(b)
                if b % 2 == 0:
                    b /= 2
                else:
                    b = 3 * b + 1
        else:
            b = 2
        if b == 1 or b == 2 or b == 4:
            b = 4
        if b == 1467 or b == 7641 or b == 6174:
            b = 6174
    if args.h:
        args.a += 1
        while not h(b):
            b += 1
        c = 0
        if (b + 1) % 6 == 0 or (b - 1) % 6 == 0:
            c += 1
        num = random.randint(1, max(1, b - 1))
        num_p = 0
        p = b
        if b != 0:
            while p > 0:
                if p % 2 == 1:
                    num_p += num
                num *= num
                p //= 2
            if num_p % b == 1:
                c += 1
            num = 1
            for i in range(b):
                num *= i
            if num % b == b - 1:
                c += 1
            match c:
                case 0:
                    b = 0
                case 1:
                    b = b + 1
                case 2:
                    b = b // 2
                case 3:
                    b = b - 1
    return b


def bad(args):
    source = taint.source()
    func(args)
    if args.a % 2 == 1 and args.count ^ args.vote ^ args.h:
        taint.sink(source)


def good(args):
    source = taint.source()
    func(args)
    if args.a % 2 == 0 and args.count ^ args.vote ^ args.h:
        taint.sink(source)
