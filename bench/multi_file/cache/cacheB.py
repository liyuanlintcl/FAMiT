from .base import Base


class CacheB(Base):
    def get(self, key):
        key = key + 'B'
        return self.dict[key]

    def set(self, key, value):
        key = key + 'B'
        self.dict[key] = value
