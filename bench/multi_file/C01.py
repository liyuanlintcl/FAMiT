from cache import cache
from bench import taint


def good(key):
    source = taint.source()
    cache.set(key, source)
    if key + 'A' in cache.dict:
        source = cache.get(key)
        taint.sink(source)


def bad(key):
    source = taint.source()
    cache.set(key, source)
    if key + 'A' not in cache.dict:
        source = cache.get(key)
        taint.sink(source)
