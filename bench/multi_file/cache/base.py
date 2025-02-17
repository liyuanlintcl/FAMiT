from abc import ABC, abstractmethod


class Base(ABC):
    def __init__(self):
        self.dict = {}

    @abstractmethod
    def get(self, key):
        pass

    @abstractmethod
    def set(self, key, value):
        pass
    