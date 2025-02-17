import importlib
import os

from .cacheA import CacheA
from .cacheB import CacheB


cache = CacheA() if os.environ.get("CACHE") == 'cacheA' else CacheB()


class CacheHandle:
    def __init__(self):
        cache_type = os.environ.get("CACHE", 'cacheA')
        cache_module = importlib.import_module('cache.' + cache_type)
        self.cache = getattr(cache_module, cache_type[0].upper() + cache_type[1:])()

    def __getattr__(self, name):
        return getattr(self.cache, name)


cache_handle = CacheHandle()
