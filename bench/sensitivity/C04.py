from bench import taint


class Singleton:
    _instances = {}

    def __init__(self, cls):
        self.cls = cls

    def __call__(self, *args, **kwargs):
        if self.cls not in self._instances:
            self._instances[self.cls] = self.cls(*args, **kwargs)
        return self._instances[self.cls]


@Singleton
class A:
    def __init__(self):
        self.x = 0

    def add(self):
        self.x += 1


def good():
    source = taint.source()
    a = A()
    b = A()
    a.add()
    if a.x != b.x:
        taint.sink(source)


def bad():
    source = taint.source()
    a = A()
    b = A()
    a.add()
    if a.x == b.x:
        taint.sink(source)
