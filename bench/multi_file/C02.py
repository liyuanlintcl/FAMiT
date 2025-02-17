from cache import cache_handle
from bench import taint


def good(key):
    source = taint.source()
    cache_handle.set(key, source)
    if key + 'A' in cache_handle.dict:
        source = cache_handle.get(key)
        taint.sink(source)


def bad(key):
    source = taint.source()
    cache_handle.set(key, source)
    if key + 'A' not in cache_handle.dict:
        source = cache_handle.get(key)
        taint.sink(source)
