from .base import Base
from bench.taint import safe


class CacheA(Base):
    def get(self, key):
        key = key + 'A'
        return self.dict[key]

    def set(self, key, value):
        key = key + 'A'
        self.dict[key] = safe(value)
