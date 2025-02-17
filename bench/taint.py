def source(x=None):
    return x if x is not None else "source"


def sink(x):
    print(x)


def safe(x=None):
    return "safe_" + x if x is not None else "safe"
