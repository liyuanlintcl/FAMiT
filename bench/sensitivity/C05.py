from bench import taint


def generator1():
    yield 1
    yield 2
    yield 3


def generator2(a):
    yield from a


def generator3():
    yield from generator1()
    yield from generator2([4, 5, 6])


def good():
    source = taint.source()
    count = 0
    for value in generator3():
        count += value
    if count != 21:
        taint.sink(source)


def bad():
    source = taint.source()
    count = 0
    for value in generator3():
        count += value
    if count == 21:
        taint.sink(source)
